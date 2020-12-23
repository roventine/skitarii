import base64

import demjson

import util.dates as dt
from intranet_infiltrator.infiltrator import Infiltrator
from util.logger import logger


class Infiltrator31ms(Infiltrator):

    def __init__(self,
                 username: str,
                 password: str):
        self.username = username
        self.password = base64.b64encode(password.encode('utf-8'))

    def infiltrate(self):
        payload = {
            'userVO.userid': self.username,
            'userVO.pwd': self.password
        }
        r = self.session.post('http://31ms.abc/privmng/To31msAuthenticationAction_usaplogin.action', data=payload)
        if r.status_code == 200:
            if r.text.index('个人信息') > 0:
                logger.info('[{}] - [{}] -> success infiltrate to 31ms '.format(self.username, self.password))

        return self

    def aim_job_list(self):
        r = self.session.post('http://31ms.abc/job/JobInfoAction_countAllJobRecord.action')
        if r.status_code == 200:
            json_obj = demjson.decode(r.text)
            job_list = json_obj['rows']
            for row in job_list:
                num_job = row['jobnum']
                name_job = row['jobTypeCN']
                if num_job != '' and int(num_job) > 0:
                    logger.info('{0} -> {1}'.format(name_job, num_job))
            return job_list

    def aim_routine_job_list(self):
        payload = {
            'start': '0',
            'limit': '100',
            'routInfoVO.setDate_Start': '',
            'routInfoVO.setDate_End': '',
            'routInfoVO.workType': '',
            'routInfoVO.workContent': '',
            'routInfoVO.jobStatus': '',
            'total': ''
        }
        r = self.session.post('http://31ms.abc/job/RoutInfoAction_findRoutInfoByWhere.action', data=payload)
        if r.status_code == 200:
            json_obj = demjson.decode(r.text)
            job_list = json_obj['rows']
            return job_list

    def obliterate_routine_job(self, routine_id, work_id):
        logger.info('{0} -> {1} aimed ...'.format(routine_id, work_id))
        payload = {
            'routRecordVO.workRequest': '',
            'routRecordVO.workDate': dt.to_current_month_end(),
            'habit': '已完成',
            'routRecordVO.workNote': '已完成',
            'routRecordVO.routId': routine_id,
            'routRecordVO.exitFlag': '0',
            'routRecordVO.Flag': dt.to_current_month_end(),
            'routRecordVO.workTipContent': '',
            'routRecordVO.workTipContent2': '',
            'routRecordVO.workTipContent3': work_id
        }
        r = self.session.post('http://31ms.abc/job/RoutRecordAction_submitPerWorkContent.action', data=payload)
        if r.status_code == 200:
            logger.info(r.json())
            logger.info('{0} -> {1} obliterated ...'.format(routine_id, work_id))

    def obliterate_routine_jobs(self):
        for routine in self.aim_routine_job_list():
            self.obliterate_routine_job(routine['routID'], routine['workID'])
