from typing import Optional
import xbmcgui

from .listing import Listing
from resources.lib.stash_interface import StashInterface
from resources.lib.utils import local, get_url
from resources.lib.navigation import NavigationItem, StudioItem, TagItem, PerformerItem


class SceneListing(Listing):
    def __init__(self, client: StashInterface):
        Listing.__init__(self, client, 'scenes', local.get_localized(30006), filter_type='SCENES')

    def get_navigation(self) -> [NavigationItem]:
        return [
            PerformerItem(self._client, 'scenes'),
            TagItem(self._client, 'scenes'),
            StudioItem(self._client, 'scenes'),
        ]

    def get_navigation_item(self, params: dict) -> Optional[NavigationItem]:
        browse = params['browse']
        if browse == 'performers':
            return PerformerItem(self._client, 'scenes')
        if browse == 'favorite_performers':
            return PerformerItem(self._client, 'scenes', favorites=True)
        if browse == 'tags':
            return TagItem(self._client, 'scenes')
        if browse == 'favorite_tags':
            return TagItem(self._client, 'scenes', favorites=True)
        if browse == 'studios':
            return StudioItem(self._client, 'scenes')

    def sort_options(self):
        return [
            (local.get_localized(30025), 'title', 'asc'),
            (local.get_localized(30026), 'created_at', 'desc'),
            (local.get_localized(30027), 'date', 'desc'),
            (local.get_localized(30020), 'random', 'asc'),
            (local.get_localized(30028), 'rating', 'desc'),
            (local.get_localized(30029), 'play_count', 'desc'),
            (local.get_localized(30030), 'last_played_at', 'desc'),
            (local.get_localized(30031), 'duration', 'desc'),
            (local.get_localized(30032), 'o_counter', 'desc'),
        ]

    def _create_items(self, criterion: dict, sort_field: str, sort_dir: str, params: dict, page=1, per_page=40):
        (count, scenes) = self._client.find_scenes(criterion, sort_field, sort_dir, page=page, per_page=per_page,
                                                   q=params.get('q'))
        sort_menu = self._context_menu(params)
        items = []
        for scene in scenes:
            item = self._create_item(scene)
            url = self._create_play_url(scene['id'])

            menu = []
            if len(scene['scene_markers']) > 0:
                menu.append((local.get_localized(30010),
                             'ActivateWindow(videos, {})'.format(get_url(list='scene_markers', scene=scene['id']))))
            menu.append(
                (local.get_localized(30008), 'RunPlugin({})'.format(get_url(increment_o='', scene=scene['id']))))
            item.addContextMenuItems(menu + sort_menu)

            items.append((item, url))

        return count, items
