from PullRequest import PullRequest

class Report:
    def __init__(self, pr: PullRequest):
        self.branch = pr.branch
        self.status = pr.status
        self.date = pr.date
        self.user =  pr.user

        # Directory Test
        self.pass_directory_test = False
        self.directory_test_report = ''

        # Configuration File Text
        self.pass_configuration_test = False
        self.configuration_test_report = ''

        # File Path Test
        self.pass_file_test = False
        self.file_test_report = ''

        # Key File Test
        self.pass_key_test = False
        self.key_test_report = ''

        # Example Data table
        self.data_preview = ''
        self.meta_data_preview = ''

        # Data Test Cases
        self.pass_data_tests = False
        self.data_tests_report = ''

        # Metadata Test Cases
        self.pass_meta_tests = False
        self.meta_tests_report = ''

        # Sample Comparison Test
        self.pass_sample_comparison = False
        self.sample_comparison_results = ''

        # Cleanup Test
        self.pass_cleanup = False
        self.cleanup_results = ''

    def __str__(self) -> str:
        out = "<h1><center>{}</center></h1>\n".format(self.branch)


