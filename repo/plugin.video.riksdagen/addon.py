# Module: addon
# Author: Tomas "tomplast" Gustavsson
# Created on: 20.01.2023
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""
riksdagen.se video plugin
"""
import xbmcgui
import xbmcplugin
import requests
import uuid
import routing
import re
import xbmc
import datetime
import html

plugin = routing.Plugin()
DEVICE_ID = str(uuid.uuid4())

def get_date(string):
    month_names = ['januari', 'februari', 'mars', 'april', 'maj', 'juni', 'juli', 'augusti', 'september', 'oktober', 'november', 'december']
    string_date, string_month, string_year = string.split()

    month =  month_names.index(string_month) + 1
    date = int(string_date)
    year = int(string_year)

    return datetime.date(year, month, date)

@plugin.route('/play_video/<id>')
def play_video(id):
    video = requests.get(
        f"https://data.riksdagen.se/api/mhs-vodapi?{id}"
        ).json()

    m3u_url = video["videodata"][0]["streams"]['files'][0]['videofileurl']

    play_item = xbmcgui.ListItem(path=m3u_url)
    xbmcplugin.setResolvedUrl(plugin.handle, True, listitem=play_item)
    

@plugin.route('/list_latest/<term>/<page>')
def list_latest(term, page):
    page = int(page)

    xbmcplugin.addDirectoryItem(
        plugin.handle,
        plugin.url_for(list_main_menu),
        xbmcgui.ListItem(label="Tillbaka till huvudmenyn.."),
        True,
    )

    url = f'https://riksdagen.se/sv/webb-tv/?p={page}'
    if term != '_':
        url += f'&q={term}'

    response = requests.get(url).text.replace('\n', '').replace('\r', '')

    if 'Din sökning gav inga träffar.' in response:
        xbmcgui.Dialog().ok('Sökresultat', 'Din sökning gav inga träffar.')
        """xbmcplugin.addDirectoryItem(
            plugin.handle,
            plugin.url_for(),
            xbmcgui.ListItem(label="Din sökning gav inga träffar!"),
            True,
        )"""
        #xbmcplugin.endOfDirectory(plugin.handle)
        return

    for item in response.split('search-item-webtv-content'):
        if 'strong' not in item:
            continue

        debate_type = re.match('.*<strong>(.*)</strong>.*', item).group(1)
        debate_date_string = ''
        debate_date_string = re.match('.*<span class="date">(.*?)</span>.*', item).group(1)

        debate_short_description = html.unescape(re.match('.*<i class="icon-play"></i></span>(.*?)[ \t]*</a>', item).group(1).strip())
        debate_video_id = re.match('.*/sv/webb-tv/video/.*?_(.*?)">.*', item).group(1)
        debate_thumbnail_url = re.match('.*(https://mhdownload.riksdagen.se/posterframe/[0-9]+\.jpg).*', item).group(1)
        debate_subtitle = re.match('.*<span class="hit-subtitle">(.*)</span>.*?', item)

        debate_date = get_date(debate_date_string)
        formatted_date = debate_date.strftime('%Y/%m/%d')
        list_item = xbmcgui.ListItem(label=f'{formatted_date} - {debate_short_description}')
        list_item.setProperty("IsPlayable", "true")

        list_item.setInfo('video', 
            {
                'title': debate_short_description, 
                'genre': debate_type, 
                'mediatype': 'video',
                'year': debate_date.year,
                'plotoutline': debate_subtitle.group(1) if debate_subtitle else ''
            }
        )

        list_item.setArt({'thumb': debate_thumbnail_url })

        xbmcplugin.addDirectoryItem(
            plugin.handle,
            plugin.url_for(play_video, id=debate_video_id),
            list_item,
            False
        )

    has_next_page = f'p={page+1}' in response
    if has_next_page:
        xbmcplugin.addDirectoryItem(
            plugin.handle,
            plugin.url_for(list_latest, term=term, page=page+1),
            xbmcgui.ListItem(label=f'Nästa sida..'),
            True,
        )

    xbmcplugin.endOfDirectory(plugin.handle)
        

@plugin.route('/search')
def search():
    term = xbmcgui.Dialog().input('Sök:')
    return list_latest(term=term, page=1)

@plugin.route("/")
def list_main_menu():
    xbmcplugin.addDirectoryItem(
        plugin.handle,
        plugin.url_for(list_latest, term='_', page=1),
        xbmcgui.ListItem(label="Senaste"),
        True,
    )

    xbmcplugin.addDirectoryItem(
        plugin.handle,
        plugin.url_for(search),
        xbmcgui.ListItem(label="Sök"),
        True,
    )

    xbmcplugin.endOfDirectory(plugin.handle)

if __name__ == "__main__":
    xbmcplugin.setPluginCategory(plugin.handle, "")
    xbmcplugin.setContent(plugin.handle, "videos")
    plugin.run()
