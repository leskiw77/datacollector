import csv
import os

import re
import shutil
import sys
from enum import Enum


class Const:
    particles_result_csv = 'result.csv'
    run_dir_prefix = 'run_'
    status_file_prefix = 'status_'
    run_result_csv_file_name = 'result.csv'
    thread_number_pattern = r'threads_(\d+)'
    thread_prefix = 'threads_'
    particles_prefix = 'particles_'


class Utils:
    @staticmethod
    def extract_thread_number(directory_name):
        return int(re.match(Const.thread_number_pattern, os.path.basename(directory_name)).group(1))


class DirectoryAction:

    def __init__(self, sub_actions=None):
        self.sub_actions: [DirectoryAction] = sub_actions
        self.current_dir = None

    """ 
    implementation can be omitted only if sub actions variable is set to None
    otherwise should return boolean informing if folder is valid subdirectory
    """
    def is_valid_subdirectory(self, dir_name):
        raise NotImplementedError

    """ actions to be taken before subactions"""
    def before(self):
        pass

    """ actions to be taken after subactions"""
    def after(self):
        pass

    """ beware that passing wrong directory do not cause any error"""
    def run(self, current_dir):
        self.current_dir = current_dir
        self._run()

    def get_valid_directories(self):
        for o in os.listdir(self.current_dir):
            if self.is_valid_subdirectory(o):
                yield os.path.join(self.current_dir, o)

    def _set_current_dir(self, current_dir):
        self.current_dir = current_dir

    def _run(self):
        if not self.current_dir:
            message = "Current dir must be set. Use set_current_dir(current_dir)"
            print(message)
            raise Exception(message)

        self.before()
        self._run_subactions()
        self.after()

    def _run_subactions(self):
        for list_dir in os.listdir(self.current_dir):
            dir_name = os.path.join(self.current_dir, list_dir)
            if os.path.isdir(dir_name) and self.is_valid_subdirectory(list_dir):
                self._run_actions(dir_name)

    def _run_actions(self, current_dir):
        if self.sub_actions:
            for action in self.sub_actions:
                action._set_current_dir(current_dir)
                action._run()


class RunInfo:
    def __init__(self):
        self.job_times = dict()
        self.collect_time: int = 0
        self.name = ''

    def add_job_time(self, job_id, job_time):
        self.job_times[job_id] = job_time


class RemoveResultRunCSV(DirectoryAction):
    def is_valid_subdirectory(self, dir_name):
        pass

    def before(self):
        file = os.path.join(self.current_dir, Const.run_result_csv_file_name)
        if os.path.isfile(file):
            os.remove(file)


class ScanRunDirs(DirectoryAction):
    def is_valid_subdirectory(self, dir_name):
        pass

    def after(self):
        results = []
        for o in os.listdir(self.current_dir):
            dir_path = os.path.join(self.current_dir, o)
            if o.startswith(Const.run_dir_prefix) and os.path.isdir(dir_path):
                status = self.get_last_status_file(dir_path)
                if status is None:
                    continue
                run_info = self.parse_status(status)
                run_info.name = o
                results.append(run_info)

        self.save_results_to_csv(os.path.join(self.current_dir, Const.run_result_csv_file_name), results)

    def save_results_to_csv(self, file_name, run_info: [RunInfo]):
        with open(file_name, 'w') as csv_file:
            fieldnames = ['name'] + ['job_' + str(number + 1) for number in range(Utils.extract_thread_number(self.current_dir))] + [
                'collect_time', 'minimum', 'maximum', 'average']

            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            writer.writeheader()

            for info in run_info:
                row = dict()
                row['name'] = info.name
                row['collect_time'] = info.collect_time

                for key, value in info.job_times.items():
                    row['job_' + str(key)] = value

                try:
                    min_time = min(info.job_times.values())
                    max_time = max(info.job_times.values())
                    avg_time = sum(info.job_times.values())/len(info.job_times.values())
                except ValueError as e:
                    print(e)
                    print('Value Error thrown when saving to {} '.format(file_name))
                    min_time = -1
                    max_time = -1
                    avg_time = -1

                row['minimum'] = min_time
                row['maximum'] = max_time
                row['average'] = avg_time

                writer.writerow(row)

    def parse_status(self, status_path):
        run_info = RunInfo()

        run_info.collect_time = self.find_collect_time(status_path)

        with open(status_path) as fp:
            var = [self.remove_multiple_spaces(row).strip() for row in fp if (row[0] != '#')]
            reader = csv.DictReader(var, delimiter=' ')
            for row in reader:
                job_id = int(row['ID'])
                job_time = int(row['TIME'])
                job_status = int(row['STATUS'])
                if job_status != 0:
                    raise Exception("Job with id {} ended with error".format(job_id))
                run_info.add_job_time(job_id, job_time)

        return run_info

    def find_collect_time(self, file_path):
        collection_header_pattern = r".*?COLLECT INFORMATION"
        collection_time_pattern = r"# TIME IN SECONDS =.*?(\d+)"

        header_regex = re.compile(collection_header_pattern)
        time_regex = re.compile(collection_time_pattern)

        class RegexAction(Enum):
            FIND_HEADER = header_regex
            FIND_COLLECTION_TIME = time_regex

        regex_action = RegexAction.FIND_HEADER
        with open(file_path) as fp:
            for row in fp:
                if regex_action.value.match(row):
                    if regex_action == RegexAction.FIND_HEADER:
                        regex_action = RegexAction.FIND_COLLECTION_TIME

                if regex_action.value.match(row):
                    if regex_action == RegexAction.FIND_COLLECTION_TIME:
                        collection_time = regex_action.value.findall(row)[0]
                        return int(collection_time)
            return 0

    def remove_multiple_spaces(self, text):
        return re.sub(' +', ' ', text)

    def get_last_status_file(self, dir_path):
        sorted_statuses = sorted([status for status in self.get_all_status_files(dir_path)])
        if sorted_statuses and len(sorted_statuses) > 0:
            return sorted_statuses[-1]
        else:
            return None

    def get_all_status_files(self, dir_path):
        for o in os.listdir(dir_path):
            file = os.path.join(dir_path, o)
            if o.startswith(Const.status_file_prefix) and os.path.isfile(file):
                yield file


class ScanThreadsDir(DirectoryAction):
    def is_valid_subdirectory(self, dir_name):
        return dir_name.startswith(Const.thread_prefix)

    def after(self):

        results = []

        for d in self.get_valid_directories():
            min_time, max_time, avg_time, collect_time = self.read_run_csv_file(d)
            thread_num = Utils.extract_thread_number(d)
            results.append({'threads_number': thread_num,
                            'minimum': self.average_from_list(min_time),
                            'maximum': self.average_from_list(max_time),
                            'average': self.average_from_list(avg_time),
                            'collect_time': self.average_from_list(collect_time),
                            })
        self.save_average_values_to_csv(results)

    def read_run_csv_file(self, dir_path):
        file = os.path.join(dir_path, Const.run_result_csv_file_name)
        with open(file) as csv_file:
            reader = csv.DictReader(csv_file)
            max_time = []
            min_time = []
            avg_time = []
            collect_time = []
            for row in reader:
                max_time.append(float(row['maximum']))
                min_time.append(float(row['minimum']))
                avg_time.append(float(row['average']))
                collect_time.append(float(row['collect_time']))
        return min_time, max_time, avg_time, collect_time

    def average_from_list(self, _list):
        if len(_list) == 0:
            return 0
        return sum(_list)/len(_list)

    def save_average_values_to_csv(self, results):
        result_file = os.path.join(self.current_dir, Const.particles_result_csv)
        with open(result_file, 'w') as csv_file:
            fieldnames = ['threads_number', 'minimum', 'maximum', 'average', 'collect_time']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for res in results:
                writer.writerow(res)


class RemoveResultThreadCSV(DirectoryAction):
    def is_valid_subdirectory(self, dir_name):
        return dir_name.startswith(Const.thread_prefix)

    def before(self):
        file = os.path.join(self.current_dir, 'result.csv')
        if os.path.isfile(file):
            os.remove(file)


class ScanParticlesDir(DirectoryAction):
    results_directory = 'stats'

    def is_valid_subdirectory(self, dir_name):
        return dir_name.startswith(Const.particles_prefix)

    def set_result_directory(self, results_directory):
        self.results_directory = results_directory

    def after(self):
        res_dir = os.path.abspath(self.results_directory)
        if not os.path.exists(self.results_directory):
            print('Creating {} directory'.format(res_dir))
            os.makedirs(self.results_directory)

        for d in self.get_valid_directories():
            # particles number
            base = os.path.basename(d)

            # filename in particle_ directory
            particle_res_file = os.path.join(d, Const.particles_result_csv)

            # copied file path
            stats_res_file = os.path.join(res_dir, base + '.csv')

            if os.path.exists(particle_res_file):
                shutil.copy(particle_res_file, stats_res_file)


class CleanParticlesDir(DirectoryAction):
    def is_valid_subdirectory(self, dir_name):
        return dir_name.startswith(Const.particles_prefix)


class Runner:
    @staticmethod
    def clean_run(experiment_directory='results'):
        run_dir_scanners = [RemoveResultRunCSV(), ScanRunDirs()]
        thread_dir_scanners = [RemoveResultThreadCSV(), ScanThreadsDir(run_dir_scanners)]
        particles_dir_scanners = ScanParticlesDir(thread_dir_scanners)
        # particles_dir_scanners.set_result_directory('results/stats')
        particles_dir_scanners.run(experiment_directory)

    @staticmethod
    def clean(experiment_directory='results'):
        run_dir_scanners = [RemoveResultRunCSV()]
        thread_dir_scanners = [RemoveResultThreadCSV(run_dir_scanners)]
        particles_dir_scanners = CleanParticlesDir(thread_dir_scanners)
        particles_dir_scanners.run(experiment_directory)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        directory_name = sys.argv[1]
    else:
        directory_name = 'results'

    Runner.clean_run(directory_name)
    # Runner.clean('results')
