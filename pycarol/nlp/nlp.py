import re
import json
import pandas as pd
from itertools import starmap

from .entity import *
from .skill import *
from ..named_query import *

class NLP:

    def __init__(self, carol):

        self.carol = carol
        self.skills = []
        self.entities = []

    # ASK A QUESTION
    def ask(self, question):
        """
        POST a query with a question
        :param question: question to be send to Carol
        :type question: str
        :return: response from request
        :rtype: str
        """        
        url_filter = "v1/ai/nlp/query/"
        data_json = {}
        data_json['question'] = question

        response = self.carol.call_api(url_filter, data=data_json)
        if 'parentSkill' in response:
            skill_name = response['parentSkill']
        matching_records = []
        if 'matchingRecords' in response: 
            for matching_record in response['matchingRecords']:
                hits = matching_record['hits']
                if len(hits) > 1:
                    matching_records.append(matching_record)
        if len(matching_records) < 1:
            return response
        else:
            partial_match = []
            for matching_record in matching_records:
                query_model = matching_record['queryModel']
                hits = matching_record['hits']
                if 'primaryKey' in matching_record:
                    primary_key = matching_record['primaryKey']
                else:
                    primary_key = None
                if 'secondaryKey' in matching_record:
                    secondary_key = matching_record['secondaryKey']
                    opts = [(hit[primary_key] + ' ' + hit[secondary_key]) for hit in hits]
                else:
                    secondaryKey = None
                    opts = [hit[primary_key] for hit in hits]
                if 'displayName' is matching_record:
                    display_name = matching_record['displayName']
                else:
                    display_name = query_model
                    
                print('\n' + display_name + ':')
                print('\n'.join(starmap('{}- {}'.format, enumerate(opts, 1))))
                user_input = input('Type the number related to the option you want: ')
                while not user_input.isdigit() or int(user_input) > len(opts):
                    if user_input.isdigit() and int(user_input) > len(opts):
                        print('Numerical input should be in the list. \n')
                    else:
                        print('Input should be a number. \n')
                    user_input = input('Type the number related to the option you want: ')
                resp = self.__fixed_query__(skill_name, query_model, hits[int(user_input) - 1])
                print('\n' + json.dumps(resp, sort_keys=True, indent=4, ensure_ascii=False))                     
            
    def __fixed_query__(self, skill_name, query_model, query_params):
        url_filter = "v1/ai/nlp/query/"
        data_json = {}
        data_json['skillName'] = skill_name
        data_json['skillQueryParams'] = {query_model : query_params}
        response = self.carol.call_api(url_filter, data=data_json)
        return response
    
    # COPY SKILLS AND ENTITIES FROM REMOTE TENANT
    def copy_data(nlp_from, nlp_to):
        """
        Copy skills and entities from a remote tenant
        :param remote_nlp: NLP object created from remote tenant
        :type remote_nlp: NLP object
        """
        skills = nlp_from.get_skills(print_response=False)
        for skill in skills:
            if skill.query_models != '{}':
                for key, value in skill.query_models.items():
                    remote_nq = NamedQuery(nlp_from.carol, page_size=10)
                    try:
                        remote_nq.named_query_data = remote_nq.by_name(value['nlpQueryName'])
                        remote_nq.named_query_data.pop('mdmId')
                        remote_nq.named_query_data.pop('mdmTenantId')
                        remote_nq.named_query_data.pop('mdmLastUpdated')
                        remote_nq.named_query_data.pop('mdmCreated')
                        local_nq = NamedQuery(nlp_to.carol).create_named_query(remote_nq.named_query_data,  overwrite=True)
                    except Exception as e:
                        print(str(e) + '\n')
            response = nlp_to.create(skill, False)
            if response is not None:
                print(skill.name + ': \n' + str(response) + '\n')

        entities = nlp_from.get_entities(print_response=False)
        for entity in entities:
            response = nlp_to.create(entity, False)
            if response is not None:
                print(entity.name + ': \n' + str(response) + '\n')
        return 'Copy finished'
        
    # GET SKILLS
    def get_skills(self, print_response=True, offset=0, page_size=100, sort_order='ASC', sort_by=None):
        """
        Get all skills from tenant
        :return: list of skills
        :rtype: list
        """ 
        url_filter = "v1/ai/skill/"        
        params = {"offset": offset, "pageSize": str(page_size), "sortOrder": sort_order}
        
        if sort_by is not None:
            params['sortBy'] = sort_by        
       
        response = self.carol.call_api(url_filter, params=params)
        for skill in response['hits']:
            _skill = Skill(skill)
            if print_response:
                print(json.dumps(skill, sort_keys=True, indent=4, ensure_ascii=False))
            self.skills.append(_skill)
        return self.skills
    
    def get_skill(self, name):
        """
        Get skill using the skill name
        :param name: skill's name
        :type name: str
        :return: Skill object
        """
        url_filter = "v1/ai/skill/name/{}".format(name)
        response = self.carol.call_api(url_filter)
        print(json.dumps(response, sort_keys=True, indent=4, ensure_ascii=False)) 
        return Skill(response)
    
    def get_skill_by_id(self, id):
        """
        Get skill using the skill id
        :param id: skill's id
        :type id: str
        :return: Skill object
        :rtype: Skill object
        """
        url_filter = "v1/ai/skill/{}".format(id)
        response = self.carol.call_api(url_filter)
        print(json.dumps(response, sort_keys=True, indent=4, ensure_ascii=False))
        return Skill(response)
    
    # GET ENTITIES
    def get_entity(self, name):
        """
        Get entity using the entity name
        :param name: entity's name
        :type name: str
        :return: Entity object
        :rtype: Entity object
        """
        url_filter = "v1/ai/skillEntity/name/{}".format(name)
        response = self.carol.call_api(url_filter)
        print(json.dumps(response, sort_keys=True, indent=4, ensure_ascii=False))
        return Entity(response)
    
    def get_entity_by_id(self, id):
        """
        Get entity using the entity id
        :param id: entity's id
        :type id: str
        :return: Entity object
        :rtype: Entity object
        """        
        url_filter = "v1/ai/skillEntity/{}".format(id)
        response = self.carol.call_api(url_filter)
        print(json.dumps(response, sort_keys=True, indent=4, ensure_ascii=False))
        return Entity(response)

    def get_entities(self, print_response=True, offset=0, page_size=100, sort_order='ASC', sort_by=None):
        """
        Get all entities from tenant
        :return: list of entities
        :rtype: list
        """  
        url_filter = "v1/ai/skillEntity"        
        params = {"offset": offset, "pageSize": str(page_size), "sortOrder": sort_order}
        
        if sort_by is not None:
            params['sortBy'] = sort_by

        response = self.carol.call_api(url_filter, params=params)
        for entity in response['hits']:
            _entity = Entity(entity)
            if print_response:
                print(json.dumps(entity, sort_keys=True, indent=4, ensure_ascii=False))
            self.entities.append(_entity)
        return self.entities
    
    # POST
    def create(self, obj, print_success=True):
        """
        Create entity/skill on tenant
        :param obj: Skill/Entity object
        :type obj: Skill/Entity object
        :return: response from request
        :rtype: str
        """            
        if isinstance(obj, Entity):
            url_filter = "v1/ai/skillEntity"
        else:
            url_filter = "v1/ai/skill"
        obj._update_json()
        try:
            response = self.carol.call_api(url_filter, method = 'POST', data=obj._json)
            if print_success:
                return response
        except Exception as e:
            return str(e)
    
    def create_from_csv(self, name_csv):
        """
        Create entities/skills on tenant from csv file
        :param name_csv: csv filename
        :type name_csv: str
        :return: response from request
        :rtype: str
        """   
        _array_fields = ['nlpValues', 'nlpRequiredEntityTypes', 'nlpOptionalEntityTypes', 'nlpAtLeastOneEntityType', 'nlpRelatedSkills']
        _answer_model_fields = ['nlpVoiceMessage', 'nlpRelatedSkills', 'nlpFallbackAnswer', 'nlpSkillAnswerData']
        data = pd.read_csv(name_csv + '.csv', sep=';')
        headers = list(data)
        for idx in range(len(data.index)):
            _json = {}
            _json['nlpAnswerModel'] = {}
            for index, item in enumerate(data.iloc[idx]):
                if pd.isnull(item):
                    pass
                else:
                    header = headers[index]
                    if header in _answer_model_fields:
                        if header == 'nlpSkillAnswerData':
                            _text_element = {}
                            _text_element['type'] = 'html'
                            _text_element['width'] = 0
                            _text_element['height'] = 0
                            _text_element['content'] = item
                            _json['nlpAnswerModel']['nlpSkillAnswerData'] = [_text_element]
                        else:
                            if header in _array_fields:
                                _array = [value for value in item.split(',')]
                                _json['nlpAnswerModel'].update({header : _array})
                            else:
                                _json['nlpAnswerModel'].update({header : item})
                    else:
                        if header in _array_fields:
                            _array = [value for value in item.split(',')]
                            _json[header] = _array
                        else:
                            _json[header] = item                        
                        
            if 'nlpValues' in headers:
                response = self.create(Entity(_json))
            else:
                response = self.create(Skill(_json))
            print(_json['nlpName'] + ': \n' + str(response) + '\n')
    
    # PUT
    def update(self, obj):
        """
        Update entity/skill on tenant
        :param obj: Skill/Entity object
        :type obj: Skill/Entity object
        :return: response from request
        :rtype: str
        """   
        if isinstance(obj, Entity):
            url_filter = "v1/ai/skillEntity/name/{}"
        else:
            url_filter = "v1/ai/skill/name/{}"
        url_filter = url_filter.format(obj.name)
        obj._update_json()
        try: 
            response = self.carol.call_api(url_filter, method = 'PUT', data=obj._json)
            return response
        except Exception as e:
            return str(e)
    
    # DELETE
    def delete_skill(self, name):
        """
        Delete skill using the skill name
        :param name: skill's name
        :type name: str
        :return: response from request
        :rtype: str
        """
        url_filter = "v1/ai/skill/name/{}".format(name)
        try: 
            response = self.carol.call_api(url_filter, method = 'DELETE')
            return response
        except Exception as e:
            return str(e)
        
    def delete_entity(self, name):
        """
        Delete entity using the entity name
        :param name: entity's name
        :type name: str
        :return: response from request
        :rtype: str
        """
        url_filter = "v1/ai/skillEntity/name/{}".format(name)
        try: 
            response = self.carol.call_api(url_filter, method = 'DELETE')
            return response
        except Exception as e:
            return str(e)