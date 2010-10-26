import string
import urllib

try:
    import pymeta
    from pymeta.grammar import OMeta
    from pymeta.runtime import ParseError
    pymeta # Ssssh, Pyflakes.
except ImportError:
    pymeta = None

from twisted.web.client import getPage

from renamer import logging
from renamer.plugin import RenamingCommand
from renamer.errors import PluginError



filenameGrammar = """
complete_strict    ::= <series_strict>:series <separator> <episode_strict>:episode
                    => series, episode
complete_lenient   ::= <series_lenient>:series <separator> <episode_lenient>:episode
                    => series, episode
partial_silly      ::= <series_silly>:series <separator> <episode_silly>:episode
                    => series, episode
only_episode_silly ::= <episode_silly>:episode
                    => None, episode
only_episode       ::= <episode_strict>:episode
                    => None, episode
only_series        ::= (<series_word>:word <separator> => word)+:words
                    => ' '.join(words), [None, None]

separator          ::= <hard_separator> | <soft_separator>
soft_separator     ::= '.' | ' ' | '-' | '_'
hard_separator     ::= ('_' '-' '_'
                       |' ' '-' ' '
                       |'.' '-' '.')

series_strict      ::= (<series_word>:word <separator> ~(<episode_strict> <separator>) => word)*:words <series_word>:word
                      => ' '.join(words + [word])
series_lenient     ::= (<series_word>:word <separator> ~(<episode_lenient> <separator>) => word)*:words <series_word>:word
                      => ' '.join(words + [word])
series_silly       ::= (<series_word>:word <soft_separator> ~(<episode_silly> <separator>) => word)*:words <separator>
                      => ' '.join(words)
series_word        ::= (<letter> | <digit>)+:name => ''.join(name)

episode_strict     ::= (<episode_x> | <episode_x2> | <episode_lettered>):ep
                      => map(''.join, ep)
episode_lenient    ::= (<episode_strict> | <episode_numbers>):ep
                      => map(''.join, ep)
episode_silly      ::= <digit>+:ep
                      => map(''.join, [ep, ep])

episode_lettered   ::= ('S' | 's') <digit>+:season ('E' | 'e') <digit>+:episode
                      => season, episode
episode_numbers    ::= <digit>:a <digit>:b <digit>:c <digit>?:d
                      => ([a, b], [c, d]) if d else ([a], [b, c])
episode_x          ::= <digit>+:season 'x' <digit>+:episode
                      => season, episode
episode_x2         ::= '[' <digit>+:season 'x' <digit>+:episode ']'
                    => season, episode
"""



class FilenameGrammar(OMeta.makeGrammar(filenameGrammar, globals())):
    pass




class TVRage(RenamingCommand):
    name = 'tvrage'


    description = 'Rename TV episodes with TV Rage metadata.'


    longdesc = """
    Extract TV episode information from filenames and rename them based on the
    correct information from TV Rage <http://tvrage.com/>.

    Available placeholders for templates are:

    series, season, padded_season, episode, padded_episode, title
    """


    defaultNameTemplate = string.Template(
        '$series [${season}x${padded_episode}] - $title')


    optParameters = [
        ('series',  None, None, 'Override series name.'),
        ('season',  None, None, 'Override season number.', int),
        ('episode', None, None, 'Override episode number.', int)]


    def postOptions(self):
        if pymeta is None:
            raise PluginError(
                'The "pymeta" package is required for this command')


    def buildMapping(self, (seriesName, season, episode, episodeName)):
        return dict(
            series=seriesName,
            season=season,
            padded_season=u'%02d' % (season,),
            episode=episode,
            padded_episode=u'%02d' % (episode,),
            title=episodeName)


    def extractParts(self, filename, overrides=None):
        """
        Get TV episode information from a filename.
        """
        if overrides is None:
            overrides = {}

        rules = ['complete_strict', 'complete_lenient']
        # We can only try the partial rules if there are some overrides.
        if filter(None, overrides.values()):
            rules.extend([
                'only_episode',
                'partial_silly',
                'only_series',
                'only_episode_silly'])

        for rule in rules:
            g = FilenameGrammar(filename)
            logging.msg('Trying grammar rule "%s"' % (rule,),
                        verbosity=5)
            try:
                res, err = g.apply(rule)
            except ParseError, e:
                try:
                    logging.msg('Parsing error:', verbosity=5)
                    for line in (e.formatError(filename).strip()).splitlines():
                        logging.msg(line, verbosity=5)
                except:
                    pass
                continue
            else:
                series, (season, episode) = res
                parts = (
                    overrides.get('series') or series,
                    overrides.get('season') or season,
                    overrides.get('episode') or episode)
                if None not in parts:
                    logging.msg('Found parts in "%s": %r' % (filename, parts),
                                verbosity=4)
                    return parts

        raise PluginError(
            'No patterns could be found in "%s"' % (filename))


    def extractMetadata(self, pageData):
        """
        Extract TV episode metadata from a TV Rage response.
        """
        data = {}
        for line in pageData.splitlines():
            key, value = line.strip().split('@', 1)
            data[key] = value.split('^')

        series = data['Show Name'][0]
        season, episode = map(int, data['Episode Info'][0].split('x'))
        title = data['Episode Info'][1]
        return series, season, episode, title


    def lookupMetadata(self, seriesName, season, episode, fetcher=getPage):
        """
        Look up TV episode metadata on TV Rage.
        """
        ep = '%dx%02d' % (int(season), int(episode))
        qs = urllib.urlencode({'show': seriesName, 'ep': ep})
        url = 'http://services.tvrage.com/tools/quickinfo.php?%s' % (qs,)
        logging.msg('Looking up TV Rage metadata at %s' % (url,),
                    verbosity=4)
        return fetcher(url).addCallback(self.extractMetadata)


    # IRenamerCommand

    def processArgument(self, arg):
        seriesName, season, episode = self.extractParts(
            arg.basename(), overrides=self)
        d = self.lookupMetadata(seriesName, season, episode)
        d.addCallback(self.buildMapping)
        return d
