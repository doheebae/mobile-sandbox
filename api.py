import json
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

class MobSF_API:
    def __init__(self, server, api_key, file_path):
        self.server = server
        self.api_key = api_key
        self.file_path = file_path
        self.scan_hash = None  

    def upload(self):
        """Upload File"""
        print("Uploading file...")
        multipart_data = MultipartEncoder(fields={'file': (self.file_path, open(self.file_path, 'rb'), 'application/octet-stream')})
        headers = {'Content-Type': multipart_data.content_type, 'Authorization': self.api_key}
        response = requests.post(self.server + '/api/v1/upload', data=multipart_data, headers=headers)
        resp_json = response.json()
        self.scan_hash = resp_json['hash']
        print("Uploaded File: ", response.text)
    
    def scan(self):
        """Scan the file"""
        if not self.scan_hash:
            print("No hash found")
            return
        print("Scanning file...")
        data = {"hash": self.scan_hash}
        headers = {'Authorization': self.api_key}
        response = requests.post(self.server + '/api/v1/scan', data=data, headers=headers)
        print("Successfully Scanned")

    def pdf(self):
        """Generate PDF Report"""
        if not self.scan_hash:
            print("No hash found")
            return
        print("Generating PDF report...")
        headers = {'Authorization': self.api_key}
        data = {'hash': self.scan_hash}
        response = requests.post(self.server + '/api/v1/download_pdf', data=data, headers=headers, stream=True)
        if response.status_code == 200:
            with open(f"static-{self.scan_hash}.pdf", 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            print(f"Report saved as static-{self.scan_hash}.pdf")
        else:
            print("Failed to download PDF report.")

    def report_json(self):
        """Generate JSON Report"""
        if not self.scan_hash:
            print("No hash found")
            return
        print("Generating JSON report")
        headers = {'Authorization': self.api_key}
        data = {"hash": self.scan_hash}
        response = requests.post(self.server + '/api/v1/report_json', data=data, headers=headers)
        if response.status_code == 200:
            report_data = response.json()
            with open("report.json", 'w') as json_file:
                json.dump(report_data, json_file, indent=4)
            print("Report saved as report.json")
        else:
            print("Failed to generate report. Status code:", response.status_code)

    def delete(self):
        """Delete Scan Result"""
        if not self.scan_hash:
            print("No hash found")
            return
        print("Deleting Scan...")
        headers = {'Authorization': self.api_key}
        data = {'hash': self.scan_hash}
        response = requests.post(self.server + '/api/v1/delete_scan', data=data, headers=headers)
        print(response.text)

    def recent_scan(self):
        headers = {'Authorization' : self.api_key}
        response = requests.get(self.server + '/api/v1/scans', headers=headers)
        scans = response.json()
        print("\033[1m\nRecent Scans:\033[0m")
        for scan in scans['content']:
            print(
                f"\nFile Name: {scan['FILE_NAME']}\n"
                f"Analyzer: {scan['ANALYZER']}\n"
                f"Scan Type: {scan['SCAN_TYPE']}\n"
                f"App Name: {scan['APP_NAME']}\n"
                f"Package Name: {scan['PACKAGE_NAME']}\n"
                f"Version Name: {scan['VERSION_NAME']}\n"
                f"MD5: {scan['MD5']}\n"
                f"Timestamp: {scan['TIMESTAMP']}\n")      

    def score(self):
        headers = {'Authorization': self.api_key}
        data = {'hash': self.scan_hash}
        response = requests.post(self.server + '/api/v1/scorecard', data=data, headers=headers)
        score_data = response.json()

        print(f"\033[1mSecurity Score: {score_data['security_score']}\033[0m")
        print(f"Total Trackers: {score_data['total_trackers']}")
        print(f"Trackers: {score_data['trackers']}")

        def print_findings(vulnerabilities, level):
            print(f"\033[1m\n[ {level} ]\033[0m")
            for vulnerability in vulnerabilities:
                print(f"\033[1m\n< {vulnerability['title']} >\033[0m")
                print(f"{vulnerability['description']}")
                print(f"({vulnerability['section']})\n")

        if 'high' in score_data:
            print_findings(score_data['high'], "High")
        if 'warning' in score_data:
            print_findings(score_data['warning'], "Warning")
        if 'info' in score_data:
            print_findings(score_data['info'], "Info")
        if 'secure' in score_data:
            print_findings(score_data['secure'], "Secure")
        if 'hotspot' in score_data:
            print_findings(score_data['hotspot'], "Hotspot")

    def compare(self):
        headers = {'Authorization': self.api_key}
        data = {'hash1': '1de07a4ceeb1c694c90ad6cad7596248', 'hash2': 'f2be9f83035f19bb37e25d3225e780e3'}
        response = requests.post(self.server + '/api/v1/compare', data=data, headers=headers)

        def print_comparison(data):
            print(f"\033[1mTitle: {data['title']}\033[0m")

            print("\033[1m\nFirst App:\033[0m")
            app_info(data['first_app'])
            print("\033[1m\nSecond App:\033[0m")
            app_info(data['second_app'])
    
            print("\033[1m\nDifferences:\033[0m")

            print_only("URLs", data['urls']['only_first'], data['urls']['only_second'])
            print_only("Android APIs", data['android_api']['only_first'], data['android_api']['only_second'])
            print_only("Permissions", data['permissions']['only_first'], data['permissions']['only_second'])
            print_only("Browsable Activities", data['browsable_activities']['only_first'], data['browsable_activities']['only_second'])
            print_only("APKID", data['apkid']['only_first'], data['apkid']['only_second'])

        def app_info(app_info):
            print(f"  Name and Version: {app_info['name_ver']}")
            print(f"  MD5: {app_info['md5']}")
            print(f"  File Name: {app_info['file_name']}")
            print(f"  Size: {app_info['size']}")
            print(f"  Icon Path: {app_info['icon_path']}")
            print(f"  Activities: {', '.join(app_info['activities'])}")
            print(f"  Services: {', '.join(app_info['services'])}")
            print(f"  Providers: {', '.join(app_info['providers'])}")
            print(f"  Receivers: {', '.join(app_info['receivers'])}")

            print("  Exported Count:")
            for key, value in app_info['exported_count'].items():
                print(f"    {key}: {value}")

            print("  APKID Information:")
            for file, details in app_info['apkid'].items():
                print(f"    {file}:")
                for check_type, checks in details.items():
                    print(f"      {check_type}: {', '.join(checks)}")

            print(f"  Certificate Subject: {app_info['cert_subject']}")

        def print_only(category, only_first, only_second):
            print(f"\n{category}:")
            if only_first:
                print("  Only in First App:")
                for item in only_first:
                    print(f"    - {item}")
            if only_second:
                print("  Only in Second App:")
                for item in only_second:
                    print(f"    - {item}")

        if response.status_code == 200:
            json_data = response.json()
            print_comparison(json_data)
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

def main():
    server_url = 'http://127.0.0.1:8000'  
    api_key = 'b8d75e09550939c951acc7f9545e2260f559eee8c51c9e237c4cce2472d4fb81'  
    file_path = '..//final.apk' 

    mobSF = MobSF_API(server_url, api_key, file_path)

    mobSF.upload()
    mobSF.scan()
    # mobSF.pdf()
    # mobSF.report_json()
    # mobSF.delete()
    # mobSF.recent_scan()
    # mobSF.score()
    # mobSF.compare()

if __name__ == "__main__":
    main()