import json
import random
import sys
from urllib.parse import parse_qsl
from typing import Optional
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
from resources.lib import utils
from resources.lib.listing import create_listing, Listing, SceneListing
from resources.lib.navigation import NavigationItem, PerformerItem, TagItem
from resources.lib.service import PLAYING_PROPERTY
from resources.lib.stash_interface import StashInterface

utils.BASE_URL = sys.argv[0]
_HANDLE = int(sys.argv[1])
NavigationItem.handle = _HANDLE
Listing.handle = _HANDLE
_ADDON = xbmcaddon.Addon()
api_key: str = ''
client: Optional[StashInterface] = None

res_map = {
    "Original": "",
    "4k": "FOUR_K",
    "1440p": "QUAD_HD",
    "FHD": "FULL_HD",
    "720p": "STANDARD_HD",
    "SD": "STANDARD",
    "240p": "LOW",
}

res_height_map = {
    "4k": 1920,
    "1440p": 1440,
    "FHD": 1080,
    "720p": 720,
    "SD": 480,
    "240p": 240,
}


def run():
    global api_key
    global client
    global playback_res
    api_key = _ADDON.getSetting('api_key')
    client = StashInterface(_ADDON.getSetting('base_url'), api_key)
    playback_res = res_map.get(_ADDON.getSetting('res'), "")
    router(sys.argv[2][1:])


def _folder(label: str, url: str, icon: str = 'DefaultFolder.png', is_folder: bool = True):
    item = xbmcgui.ListItem(label=label)
    item.setArt({'icon': icon})
    xbmcplugin.addDirectoryItem(_HANDLE, url, item, is_folder)


def browse_root():
    xbmcplugin.setPluginCategory(_HANDLE, 'Stash')
    xbmcplugin.setContent(_HANDLE, 'videos')

    loc = utils.local.get_localized
    _folder(loc(30016), utils.get_url(search='scenes'), 'DefaultAddonsSearch.png', is_folder=False)
    _folder(loc(30017), utils.get_url(list='scenes', title=loc(30017), sort_field='created_at', sort_dir='desc'),
            'DefaultRecentlyAddedMovies.png')
    _folder(loc(30018), utils.get_url(list='scenes', title=loc(30018), sort_field='last_played_at', sort_dir='desc',
                                      criterion=json.dumps({'resume_time': {'modifier': 'GREATER_THAN', 'value': 0}})),
            'DefaultInProgressShows.png')
    _folder(loc(30019), utils.get_url(list='scenes', title=loc(30019), sort_field='last_played_at', sort_dir='desc',
                                      criterion=json.dumps({'play_count': {'modifier': 'GREATER_THAN', 'value': 0}})),
            'DefaultRecentlyAddedEpisodes.png')
    _folder(loc(30020), utils.get_url(list='scenes', title=loc(30020), sort_field=random_sort()))
    for favorites in (PerformerItem(client, 'scenes', favorites=True), TagItem(client, 'scenes', favorites=True)):
        (item, url) = favorites.get_root_item()
        xbmcplugin.addDirectoryItem(_HANDLE, url, item, True)

    listing = SceneListing(client)
    for (item, url) in listing.get_filters():
        xbmcplugin.addDirectoryItem(_HANDLE, url, item, True)

    (item, url) = listing.get_root_item(loc(30002))
    xbmcplugin.addDirectoryItem(_HANDLE, url, item, True)

    for navItem in listing.get_navigation():
        (item, url) = navItem.get_root_item()
        xbmcplugin.addDirectoryItem(_HANDLE, url, item, True)

    item = xbmcgui.ListItem(label=loc(30010))
    url = utils.get_url(browse='scene_markers')
    xbmcplugin.addDirectoryItem(_HANDLE, url, item, True)

    xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(_HANDLE)


def browse(params):
    xbmcplugin.setPluginCategory(_HANDLE, 'Stash')
    xbmcplugin.setContent(_HANDLE, 'videos')

    listing = create_listing(params['browse'], client)
    for (item, url) in listing.get_filters():
        xbmcplugin.addDirectoryItem(_HANDLE, url, item, True)

    (item, url) = listing.get_root_item(utils.local.get_localized(30002))
    xbmcplugin.addDirectoryItem(_HANDLE, url, item, True)

    for navItem in listing.get_navigation():
        (item, url) = navItem.get_root_item()
        xbmcplugin.addDirectoryItem(_HANDLE, url, item, True)

    xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(_HANDLE)


def list_items(params: dict):
    listing = create_listing(params['list'], client)
    listing.list_items(params)


def browse_for(params: dict):
    listing = create_listing(params['browse_for'], client)
    navigation = listing.get_navigation_item(params)
    navigation.list_items(params)


def random_sort() -> str:
    # A seed keeps the order stable while paging, like the random sort in Stash' UI
    return 'random_{}'.format(random.randint(0, 99999999))


def search(params: dict):
    loc = utils.local.get_localized
    query = xbmcgui.Dialog().input(loc(30037))
    if query:
        url = utils.get_url(list=params['search'], q=query, title='{}: {}'.format(loc(30016), query),
                            sort_field='date', sort_dir='desc')
        xbmc.executebuiltin('Container.Update({})'.format(url))


def choose_sort(params: dict):
    listing = create_listing(params.pop('choose_sort'), client)
    options = listing.sort_options()
    labels = [label for (label, _, _) in options] + [utils.local.get_localized(30033)]
    choice = xbmcgui.Dialog().select(utils.local.get_localized(30024), labels)
    if choice < 0:
        return

    params.pop('page', None)
    if choice == len(options):
        params['sort_dir'] = 'asc' if params.get('sort_dir', 'asc').lower() == 'desc' else 'desc'
    else:
        (_, field, direction) = options[choice]
        params['sort_field'] = random_sort() if field == 'random' else field
        params['sort_dir'] = direction

    xbmc.executebuiltin('Container.Update({},replace)'.format(utils.get_url(**params)))


def get_mp4_stream(sceneStreams: dict) -> str:
    for stream in sceneStreams:
        if stream["label"] == "DASH":
            return stream


def play(params: dict):
    scene = client.find_scene(params['play'])
    item = xbmcgui.ListItem()
    if playback_res != "" and scene["files"][0]["height"] > res_height_map[_ADDON.getSetting('res')]:
        stream = get_mp4_stream(scene["sceneStreams"])
        url = stream["url"].replace("ORIGINAL", playback_res)
        item.setMimeType('application/xml+dash')
        item.setContentLookup(False)

        item.setProperty('inputstream', 'inputstream.adaptive')
        item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        item.setProperty('inputstream.adaptive.stream_headers',
                         f'apikey={api_key}')
        item.setProperty('inputstream.adaptive.manifest_headers',
                         f'apikey={api_key}')
        item.setPath(url)
    else:
        streamurl = scene['paths']['stream']
        item.setPath(streamurl)

    xbmcplugin.setResolvedUrl(_HANDLE, True, listitem=item)


def increment_o(params: dict):
    # Without a scene: the scene currently playing, so this can be bound to a key, e.g. in a keymap:
    # <key>RunPlugin(plugin://plugin.video.stash/?increment_o)</key>
    scene = params.get('scene') or xbmcgui.Window(10000).getProperty(PLAYING_PROPERTY)
    if scene:
        o_count = client.scene_add_o(scene)
        xbmc.executebuiltin('Notification(Stash, {} {})'.format(utils.local.get_localized(30009), o_count))


def set_favorite(params: dict):
    client.set_favorite(params['set_favorite'], params['id'], params.get('value') == '1')
    xbmc.executebuiltin('Container.Refresh')


def rate_scene(params: dict):
    loc = utils.local.get_localized
    labels = [loc(30043)] + ['★' * stars + '☆' * (5 - stars) for stars in range(1, 6)]
    choice = xbmcgui.Dialog().select(loc(30041), labels)
    if choice >= 0:
        client.set_scene_rating(params['rate_scene'], choice * 20 if choice else None)
        xbmc.executebuiltin('Container.Refresh')


def scene_performers(params: dict):
    performers = client.find_scenes({'id': {'modifier': 'EQUALS', 'value': int(params['scene_performers'])}},
                                    per_page=1)[1][0]['performers']
    labels = [('★ ' if p['favorite'] else '☆ ') + p['name'] for p in performers]
    choice = xbmcgui.Dialog().select(utils.local.get_localized(30044), labels)
    if choice >= 0:
        performer = performers[choice]
        favorite = client.set_favorite('performer', performer['id'], not performer['favorite'])
        xbmc.executebuiltin('Notification(Stash, {}: {})'.format(
            performer['name'], utils.local.get_localized(30045 if favorite else 30046)))


def router(param_string: str):
    params = dict(parse_qsl(param_string, keep_blank_values=True))

    if params:
        if 'choose_sort' in params:
            choose_sort(params)
        elif 'search' in params:
            search(params)
        elif 'browse_for' in params:
            browse_for(params)
        elif 'browse' in params:
            browse(params)
        elif 'list' in params:
            list_items(params)
        elif 'play' in params:
            play(params)
        elif 'increment_o' in params:
            increment_o(params)
        elif 'set_favorite' in params:
            set_favorite(params)
        elif 'rate_scene' in params:
            rate_scene(params)
        elif 'scene_performers' in params:
            scene_performers(params)
    else:
        browse_root()
