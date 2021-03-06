import math, sys
from mediacloud.storage import MongoStoryDatabase
from bson.code import Code
from mediameter.cliff import Cliff

CLIFF_RESULTS_ATTR = "cliffResults"
CLIFF_COUNTRIES_FOCUS_ATTR = "cliffCountriesOfFocus"

class GeoStoryDatabase(MongoStoryDatabase):
    '''
    '''

    def storiesWithoutCliffInfo(self, limit=None):
        cursor = self._db.stories.find({ CLIFF_RESULTS_ATTR: {'$exists':False} })
        if limit is not None:
            cursor.limit(limit)
        return cursor

    def storiesWithCliffInfo(self, limit=None):
        cursor = self._db.stories.find({ CLIFF_RESULTS_ATTR: {'$exists':True} })
        if limit is not None:
            cursor.limit(limit)
        return cursor

    def allStories(self):
        return self._db.stories.find()

    def maxStoryProcessedId(self,media_id=None):
        res = self._db.stories.find({'media_id':int(media_id)}).sort('processed_stories_id',-1).limit(1)
        if res.count()==0:
            return 0
        else:
            return res[0]['processed_stories_id']

    def mediaStoryCounts(self):
        '''
        Returns dict of media_id=>story_count
        '''
        key = ['media_id']
        condition = {}
        initial = {'value':0}
        reduce = Code("function(doc,prev) { prev.value += 1; }") 
        raw_results = self._db.stories.group(key, condition, initial, reduce);
        return self._resultsToDict(raw_results,'media_id')

    def mediaTypeStoryCounts(self):
        '''
        Returns dict of media_type=>story_count
        '''
        key = ['type']
        condition = {}
        initial = {'value':0}
        reduce = Code("function(doc,prev) { prev.value += 1; }") 
        raw_results = self._db.stories.group(key, condition, initial, reduce);
        return self._resultsToDict(raw_results,'type')

    def allAboutCountries(self, media_type=None):
        cursor = self._db.stories
        if media_type is not None:
            cursor = cursor.find({'type': media_type})
        return cursor.distinct(CLIFF_COUNTRIES_FOCUS_ATTR)

    def storiesOfType(self,media_type,country_alpha2=None):
        criteria = {'type': media_type }
        if country_alpha2 is not None:
            criteria[CLIFF_COUNTRIES_FOCUS_ATTR] = country_alpha2
        return self._db.stories.find(criteria)

    def storiesFromSource(self,media_id,country_alpha2=None):
        criteria = {'media_id': int(media_id) }
        if country_alpha2 is not None:
            criteria[CLIFF_COUNTRIES_FOCUS_ATTR] = country_alpha2
        return self._db.stories.find(criteria)

    def peopleMentioned(self, media_type, country_alpha2=None):
        name_to_count = {}
        criteria = { 'type': media_type }
        if country_alpha2 is not None:
            criteria[CLIFF_COUNTRIES_FOCUS_ATTR] = country_alpha2
        for doc in self._db.stories.find(criteria):
            for info in doc[CLIFF_RESULTS_ATTR]['results']['people']:
                if info['name'] not in name_to_count.keys():
                    name_to_count[info['name']] = info['count']
                else:
                    name_to_count[info['name']] += info['count']
        return name_to_count

    # assumes key is integer!
    def _resultsToDict(self, raw_results, id_key):
        ''' 
        Helper to change a key-value set of results into a python dict
        '''
        results = {}
        for doc in raw_results:
            key_ok = False
            try:
                # first make sure key is an integer
                throwaway = doc[id_key]
                # now check optional range
                if throwaway=='?' or throwaway=='NULL':
                    key_ok = False
                else:
                    key_ok = True
            except:
                # we got NaN, so ignore it
                key_ok = False
            if key_ok:
                key_to_use = doc[id_key]
                if isinstance(key_to_use, list):
                    if len(key_to_use)==0:
                        key_to_use = None
                    else:
                        key_to_use = key_to_use[0]
                if key_to_use is not None:
                    try:
                        key_to_use = int(key_to_use)
                    except ValueError, TypeError:
                        key_to_use = key_to_use
                    results[ key_to_use ] = int(doc['value'])
        return results
