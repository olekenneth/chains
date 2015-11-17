import chains.service
from chains.common import log
import time, datetime, re, copy
from soco import SoCo, discover

class SonosService(chains.service.Service):

    def onInit(self):

        # Discover Sonos players
        self.zones = list(discover())

        # Set default player
        self.defaultZone = None
        if self.zones:
            defaultZone = self.config.get('defaultzone')
            if defaultZone:
                self.defaultZone = self.getZone(defaultZone)
            else:
                self.defaultZone = self.zones[0]
            
        

    def getZone(self, nameOrId):
        for zone in self.zones:
            if zone.uid == nameOrId:
                return zone
            if zone.player_name == nameOrId:
                return zone
        return self.defaultZone

    def action_play(self, zone=None):
        zone = self.getZone(zone)
        zone.play()

    def action_stop(self, zone=None):
        zone = self.getZone(zone)
        zone.stop()

    def action_playUri(self, uri, zone=None, volume=None, playmode=None):
        zone = self.getZone(zone)

        if volume:
            log.info('vol:%s'%volume)
            zone.volume = int(volume)
        if playmode:
            log.info('mode:%s'%playmode)
            zone.play_mode = playmode

        log.info('zone: %s' % zone)
        log.info('playUri: %s' % uri)

        zone.play_uri(uri)

    def action_setPlayMode(self, mode, zone=None):
        zone = self.getZone(zone)
        zone.play_mode = mode

    def action_getPlaylistNames(self):
        zone = self.getZone(zone)
        playlists = soc.get_music_library_information('sonos_playlists')
        result = []
        for playlist in playlists:
            result.append( playlist.title )
        return result

    def action_getPlaylistDicts(self):
        zone = self.getZone(zone)
        playlists = soc.get_music_library_information('sonos_playlists')
        result = []
        for playlist in playlists:
            result.append( playlist.to_dict )
        return result

    def action_getPlaylistTracks(self, playlist_name):
        zone = self.getZone(zone)
        playlists = soc.get_music_library_information('sonos_playlists')
        result = []
        for playlist in playlists:
            if playlist.title == playlist_name:
                track_list = zone.browse(playlist)
                for item in track_list:
                    result.append({
                        title: item.title,
                        album: item.album,
                        artist: item.creator,
                        uri:   item.uri,
                        art:   item.album_art_uri
                    })
                return result
        return result

    def action_playPlaylist(self, name, zone=None, volume=None, playmode=None):
        zone = self.getZone(zone)

        if volume:
            log.info('vol:%s'%volume)
            zone.volume = int(volume)
        if playmode:
            log.info('mode:%s'%playmode)
            zone.play_mode = playmode

        log.info('pls')
        playlists = zone.get_sonos_playlists()
        if not playlists:
            return False
        found = None
        for playlist in playlists:
            if playlist.title.lower().strip() == name.lower().strip():
                found = playlist
                break
        if not found:
            return False
        zone.clear_queue()
        zone.add_to_queue(playlist)
        zone.play_from_queue(0)

    def action_setVolume(self, volume, zone=None):
        zone = self.getZone(zone)
        zone.volume = int(volume)

    def action_getVolume(self, zone=None):
        zone = self.getZone(zone)
        return zone.volume

    def action_modifyVolume(self,amount, zone=None):
        zone = self.getZone(zone)
        amount = int(amount)
        zone.volume += amount

    def action_getTrackInfo(self, zone=None):
        zone = self.getZone(zone)
        info = zone.get_current_track_info()
        del info['metadata']
        return info

    def action_getTrackMetaData(self, zone=None):
        zone = self.getZone(zone)
        info = zone.get_current_track_info()
        return info['metadata']

    def action_getTrackUri(self, zone=None):
        zone = self.getZone(zone)
        info = zone.get_current_track_info()
        if not info:
            return None
        return info.get('uri')

    def action_clearQueue(self, zone=None):
        zone = self.getZone(zone)
        zone.clear_queue()

    def action_join(self, slaveZone, masterZone=None):
        slaveZone = self.getZone(slaveZone)
        masterZone = self.getZone(masterZone)
        slaveZone.join(masterZone)

    def action_unjoin(self, slaveZone):
        slaveZone = self.getZone(slaveZone)
        slaveZone.unjoin()

    def action_list(self):
        result = []
        for zone in self.zones:
            #result.append({
            #    'name': zone.player_name,
            #    'id':   zone.uid
            #})
            result.append(zone.get_speaker_info())
        return result

