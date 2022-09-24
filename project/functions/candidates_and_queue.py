from models.models import WeightcategoriesDB, RegistrationsDB
from sqlalchemy import desc, asc
from extensions import extensions
from flask import render_template, jsonify

db = extensions.db


def candidates_and_queue(candidates_data, backlog_data, fights_data, round_id):
    """То что передается в блоки кандидатов и очереди нераспределенных"""
    red_candidate_reg_id = 0
    blue_candidate_reg_id = 0
    # print(candidates_data)
    if candidates_data:
        if candidates_data.red_candidate_reg_id:
            red_candidate_reg_id = candidates_data.red_candidate_reg_id
        if candidates_data.blue_candidate_reg_id:
            blue_candidate_reg_id = candidates_data.blue_candidate_reg_id
            if red_candidate_reg_id == 0 and blue_candidate_reg_id == 0:
                return {'htmlresponse_red_candidate': render_template('empty_candidate.html'),
                        'htmlresponse_blue_candidate': render_template('empty_candidate.html'),
                        'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                        'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),
                        }

            elif red_candidate_reg_id != 0 and blue_candidate_reg_id == 0:
                red_candidate_last_name = candidates_data.red_candidate_reg.registration_participant.participant_last_name
                red_candidate_first_name = candidates_data.red_candidate_reg.registration_participant.participant_first_name
                return {'htmlresponse_red_candidate': render_template('red_candidate.html',
                                                                      red_candidate_last_name=red_candidate_last_name,
                                                                      red_candidate_first_name=red_candidate_first_name,
                                                                      round_id=round_id),
                        'htmlresponse_blue_candidate': render_template('empty_candidate.html'),
                        'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                        'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),
                        }

            elif red_candidate_reg_id == 0 and blue_candidate_reg_id != 0:
                blue_candidate_last_name = candidates_data.blue_candidate_reg.registration_participant.participant_last_name
                blue_candidate_first_name = candidates_data.blue_candidate_reg.registration_participant.participant_first_name
                return {'htmlresponse_red_candidate': render_template('empty_candidate.html'),
                        'htmlresponse_blue_candidate': render_template('blue_candidate.html',
                                                                       blue_candidate_last_name=blue_candidate_last_name,
                                                                       blue_candidate_first_name=blue_candidate_first_name,
                                                                       round_id=round_id),
                        'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                        'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),

                        }
            else:
                red_candidate_last_name = candidates_data.red_candidate_reg.registration_participant.participant_last_name
                red_candidate_first_name = candidates_data.red_candidate_reg.registration_participant.participant_first_name
                blue_candidate_last_name = candidates_data.blue_candidate_reg.registration_participant.participant_last_name
                blue_candidate_first_name = candidates_data.blue_candidate_reg.registration_participant.participant_first_name
                return {'htmlresponse_red_candidate': render_template('red_candidate.html',
                                                                      red_candidate_last_name=red_candidate_last_name,
                                                                      red_candidate_first_name=red_candidate_first_name,
                                                                      round_id=round_id),
                        'htmlresponse_blue_candidate': render_template('blue_candidate.html',
                                                                       blue_candidate_last_name=blue_candidate_last_name,
                                                                       blue_candidate_first_name=blue_candidate_first_name,
                                                                       round_id=round_id),
                        'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                        'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),

                        }
        else:
            return {'htmlresponse_red_candidate': render_template('empty_candidate.html'),
                    'htmlresponse_blue_candidate': render_template('empty_candidate.html'),
                    'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                    'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),
                    }
