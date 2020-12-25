import base64
from hashlib import md5

import demjson
import requests
from lxml import html

import util.dates as dt
from intranet_infiltrator.infiltrator import Infiltrator
from util.logger import logger

headers = {
    'Accept': '*/*',
    'Content-Type': 'text/plain',
    'Referer': 'http://web.els.abc/student/courseCenter/',
    'Accept-Language': 'zh-Hans-CN,zh-Hans;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Host': 'web.els.abc',
    'Connection': 'Keep-Alive',
    'Pragma': 'no-cache',
}


class Infiltrator:

    def __init__(self):
        self.session = requests.session()

    def active(self):
        return self


class InfiltratorTo31ms(Infiltrator):

    def __init__(self,
                 username: str,
                 password: str):
        Infiltrator.__init__(self)
        self.username = username
        self.password = base64.b64encode(password.encode('utf-8'))

    def active(self):
        return self.infiltrate().obliterate_routine_jobs()

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
        return self


class InfiltratorToELS(Infiltrator):

    def __init__(self,
                 username: str,
                 password: str):
        Infiltrator.__init__(self)
        self.username = username
        self.password = md5(password.encode('utf-8')).hexdigest()
        self.compulsory_courses = {}

    def active(self):
        return self.infiltrate().obliterate_routine_jobs()

    def infiltrate(self):
        r = self.session.post('http://web.els.abc/')
        if r.status_code == 200:
            tree = html.fromstring(r.text)
            token = tree.xpath('//input[@name="token"]')[0].value
            data = {
                'token': token,
                'j_username': self.username,
                'j_password': self.password,
                'struts.token.name': 'token'
            }
            r = self.session.post('http://web.els.abc/j_acegi_security_check', data=data)
            if r.status_code == 200:
                r = self.session.get('http://web.els.abc/signUp.action')
                if r.status_code == 200:
                    r = self.session.get('http://web.els.abc/student/index.action')
                    if r.status_code == 200:
                        if r.text.find('error') > 0:
                            logger.error('{0} - {1} -> login failed', self.username, self.password)
                        else:
                            logger.info('{0} - {1} -> login success', self.username, self.password)
        return self

    def get_compulsory_courses(self):
        data = {
            'ec_i': 'CourseCenterActionForm',
            'CourseCenterActionForm_crd': '100',
            'CourseCenterActionForm_p': '1',
            'CourseCenterActionForm_totalpages': '4',
            'CourseCenterActionForm_totalrows': '42',
            'CourseCenterActionForm_pg': '1',
            'CourseCenterActionForm_rd': '100'
        }
        r = self.session.get('http://web.els.abc/student/courseCenter/showOrgPlanCourse.action',
                             params=data,
                             headers=headers)
        if r.status_code == 200:
            tree = html.fromstring(r.text)
            titles = tree.xpath('//*[@id="CourseCenterActionForm_table_body"]/tr/td[1]/a/text()')
            courses = tree.xpath('//*[@id="CourseCenterActionForm_table_body"]/tr/td[7]/a/@href')
            for i in range(len(courses)):
                course = courses[i]
                title = titles[i]
                course = 'http://web.els.abc' + str(course) \
                    .replace('javascript:doLearnOpenCourse(\'', '') \
                    .replace('\')', '')
                self.compulsory_courses[title] = course
        return self

    def is_contains_single_select(questions):
        answers = []
        for question in questions:
            question_typ = question.split(',')[2]
            if question_typ == '6':
                question_id = question.split(',')[0].replace(' = new StudentQuestion("', '').replace('"', '')
                for raw_answer in question.split('Answer')[1:]:
                    answers.append(raw_answer.split(',')[0].replace('\"', '').replace('(', ''))
                return question_id, answers

    def is_contains_judge(self,questions):
        for question in questions:
            question_typ = question.split(',')[2]
            if question_typ == '2':
                question_id = question.split(',')[0].replace(' = new StudentQuestion("', '').replace('"', '')
                return question_id

    def is_pass(self,msg):
        return msg.find('恭喜') > 0

    def finish_quiz(self,id_course, id_quiz):
        url_do_quiz = 'http://web.els.abc/student/courseCenter/doExam.action?id=' + id_course + '&rcoId=' + id_quiz
        r = self.session.get(url_do_quiz, headers=headers)
        data = {}
        if r.status_code == 200:
            tree = html.fromstring(r.text)
            quiz_post_form_inputs = tree.xpath('//form[@name="examPaperForm"]/input[@type="hidden"]')
            for input in quiz_post_form_inputs:
                data[input.name] = input.value

            str_fragment_script = tree.xpath('//script[contains(text(),"var tStuExam")]/text()')[0]
            i_start = str(str_fragment_script).index('var tStuPaper', 0)
            i_end = str(str_fragment_script).index('var tPaperType', 0)

            # quiz_point -- maybe there is a mistake
            quiz_point = str_fragment_script[i_start:i_end].split(',')[3]
            quiz_point2 = str_fragment_script[i_start:i_end].split(',')[4]
            if str(quiz_point).replace("\"", "") != '100' and int(quiz_point2) == 100:
                quiz_point = 100

            questions = str_fragment_script.split('var stuQu')
            question_id = is_contains_judge(questions)

            headers["Content-type"] = "application/x-www-form-urlencoded"

            if question_id is not None:
                # print('we have a judge question ')
                # judge question has values -1 1,and we will post data twice
                data['questionId'] = question_id
                data['questionType' + question_id] = '2'
                data['questionPoint' + question_id] = quiz_point
                data['answer_' + question_id] = '1'
                r = s.post('http://web.els.abc/student/courseCenter/examSubmit.action', data=data, headers=headers)
                if r.status_code == 200:
                    # print(r.text)
                    if is_pass(r.text):
                        print('pass')
                        return
                    else:
                        data['answer_' + question_id] = '-1'
                        r = s.post('http://web.els.abc/student/courseCenter/examSubmit.action', data=data, headers=headers)
                        if r.status_code == 200:
                            if is_pass(r.text):
                                print('pass')
                                return
            else:
                question_id, answers = is_contains_single_select(questions)
                for answer in answers:
                    data['questionId'] = question_id
                    data['questionType' + question_id] = '6'
                    data['questionPoint' + question_id] = quiz_point
                    data['answer_' + question_id] = answer
                    r = s.post('http://web.els.abc/student/courseCenter/examSubmit.action', data=data, headers=headers)
                    if r.status_code == 200:
                        if is_pass(r.text):
                            print('pass')
                            return