import paramiko
import yaml
import json
from datetime import datetime
import os
import re

class NetworkAuditor:
    """Main auditor class for security compliance checking"""
    
    def __init__(self, inventory_file, baselines_dir):
        """
        Initialize the auditor with device inventory and baseline configurations
        
        Args:
            inventory_file: Path to device inventory YAML file
            baselines_dir: Path to directory containing baseline YAML files
        """
        self.inventory_file = inventory_file
        self.baselines_dir = baselines_dir
        self.devices = []
        self.baselines = {}
        self.audit_results = []
        
    def load_inventory(self):
        """Load device inventory from YAML file"""
        with open(self.inventory_file, 'r') as f:
            data = yaml.safe_load(f)
            self.devices = data['devices']
        print(f"✓ Loaded {len(self.devices)} devices from inventory")
    
    def load_baselines(self):
        """Load all baseline configuration files"""
        baseline_files = ['ssh_baseline.yaml', 'users_baseline.yaml', 'firewall_baseline.yaml']
        
        for filename in baseline_files:
            filepath = os.path.join(self.baselines_dir, filename)
            with open(filepath, 'r') as f:
                baseline_name = filename.replace('_baseline.yaml', '')
                self.baselines[baseline_name] = yaml.safe_load(f)
        
        print(f"✓ Loaded {len(self.baselines)} baseline configurations")
    
    def ssh_connect(self, device):
        """
        Establish SSH connection to a device
        
        Args:
            device: Dictionary containing device connection info
            
        Returns:
            SSH client object or None if connection fails
        """
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=device['ip'],
                username=device['username'],
                password=device['password'],
                timeout=10
            )
            return client
        except Exception as e:
            print(f"✗ Failed to connect to {device['hostname']}: {e}")
            return None
    
    def extract_ssh_config(self, ssh_client):
        """
        Extract SSH configuration from remote device
        
        Args:
            ssh_client: Active SSH client connection
            
        Returns:
            Dictionary of SSH configuration parameters
        """
        stdin, stdout, stderr = ssh_client.exec_command('sudo cat /etc/ssh/sshd_config')
        config_text = stdout.read().decode()
        
        config = {}
        for line in config_text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                match = re.match(r'(\w+)\s+(.+)', line)
                if match:
                    key, value = match.groups()
                    config[key] = value.strip()
        
        return config
    
    def extract_user_accounts(self, ssh_client):
        """
        Extract user account information from /etc/passwd
        
        Args:
            ssh_client: Active SSH client connection
            
        Returns:
            List of usernames
        """
        stdin, stdout, stderr = ssh_client.exec_command('cat /etc/passwd')
        passwd_text = stdout.read().decode()
        
        users = []
        for line in passwd_text.split('\n'):
            if line:
                username = line.split(':')[0]
                # Only include regular user accounts (UID >= 1000)
                stdin, stdout, stderr = ssh_client.exec_command(f'id -u {username}')
                try:
                    uid = int(stdout.read().decode().strip())
                    if uid >= 1000:
                        users.append(username)
                except:
                    pass
        
        return users
    
    def extract_firewall_rules(self, ssh_client):
        """
        Extract firewall rules using ufw
        
        Args:
            ssh_client: Active SSH client connection
            
        Returns:
            List of firewall rules
        """
        stdin, stdout, stderr = ssh_client.exec_command('sudo ufw status numbered')
        output = stdout.read().decode()
        
        rules = []
        for line in output.split('\n'):
            if 'ALLOW' in line or 'DENY' in line or 'REJECT' in line:
                rules.append(line.strip())
        
        return rules
    
    def audit_ssh_config(self, device_name, ssh_config):
        """
        Audit SSH configuration against baseline
        
        Args:
            device_name: Name of the device being audited
            ssh_config: Extracted SSH configuration
            
        Returns:
            List of violations found
        """
        violations = []
        baseline = self.baselines['ssh']
        
        for rule in baseline.get('compliance_rules', []):
            parameter = rule['parameter']
            expected = rule['expected']
            actual = ssh_config.get(parameter, 'not set')
            
            if str(actual).lower() != str(expected).lower():
                violations.append({
                    'device': device_name,
                    'category': 'SSH Configuration',
                    'rule': rule['rule'],
                    'severity': rule['severity'],
                    'parameter': parameter,
                    'expected': expected,
                    'actual': actual,
                    'remediation': f"Set {parameter} to {expected} in /etc/ssh/sshd_config"
                })
        
        return violations
    
    def audit_user_accounts(self, device_name, users):
        """
        Audit user accounts against baseline
        
        Args:
            device_name: Name of the device being audited
            users: List of user accounts found
            
        Returns:
            List of violations found
        """
        violations = []
        baseline = self.baselines['users']
        
        # Check for required users
        for req_user in baseline.get('required_users', []):
            if req_user['username'] not in users:
                violations.append({
                    'device': device_name,
                    'category': 'User Accounts',
                    'rule': req_user['description'],
                    'severity': req_user['severity'],
                    'parameter': 'required_user',
                    'expected': req_user['username'],
                    'actual': 'not found',
                    'remediation': f"Create user account: {req_user['username']}"
                })
        
        # Check for prohibited users
        for prohibited in baseline.get('prohibited_users', []):
            if prohibited['username'] in users:
                violations.append({
                    'device': device_name,
                    'category': 'User Accounts',
                    'rule': prohibited['description'],
                    'severity': prohibited['severity'],
                    'parameter': 'prohibited_user',
                    'expected': 'should not exist',
                    'actual': prohibited['username'],
                    'remediation': f"Remove user account: sudo userdel {prohibited['username']}"
                })
        
        return violations
    
    def audit_firewall_rules(self, device_name, firewall_rules):
        """
        Audit firewall rules against baseline
        
        Args:
            device_name: Name of the device being audited
            firewall_rules: List of firewall rules
            
        Returns:
            List of violations found
        """
        violations = []
        baseline = self.baselines['firewall']
        
        # Check for blocked rules that shouldn't be allowed
        for blocked in baseline.get('blocked_rules', []):
            port = str(blocked['port'])
            for rule in firewall_rules:
                if port in rule and 'ALLOW' in rule:
                    violations.append({
                        'device': device_name,
                        'category': 'Firewall Rules',
                        'rule': blocked['description'],
                        'severity': blocked['severity'],
                        'parameter': f"port_{port}",
                        'expected': 'blocked',
                        'actual': 'allowed',
                        'remediation': f"Block port {port}: sudo ufw deny {port}/{blocked['protocol']}"
                    })
        
        return violations
    
    def calculate_security_score(self, violations):
        """
        Calculate security score based on violations
        
        Args:
            violations: List of violation dictionaries
            
        Returns:
            Integer score from 0-100
        """
        score = 100
        
        for violation in violations:
            if violation['severity'] == 'critical':
                score -= 15
            elif violation['severity'] == 'warning':
                score -= 5
        
        return max(0, score)  # Ensure score doesn't go below 0
    
    def audit_device(self, device):
        """
        Perform complete audit on a single device
        
        Args:
            device: Device dictionary from inventory
            
        Returns:
            Audit result dictionary
        """
        print(f"\n{'='*60}")
        print(f"Auditing: {device['hostname']} ({device['ip']})")
        print(f"{'='*60}")
        
        ssh_client = self.ssh_connect(device)
        if not ssh_client:
            return None
        
        try:
            # Extract configurations
            print("→ Extracting SSH configuration...")
            ssh_config = self.extract_ssh_config(ssh_client)
            
            print("→ Extracting user accounts...")
            users = self.extract_user_accounts(ssh_client)
            
            print("→ Extracting firewall rules...")
            firewall_rules = self.extract_firewall_rules(ssh_client)
            
            # Perform audits
            violations = []
            violations.extend(self.audit_ssh_config(device['hostname'], ssh_config))
            violations.extend(self.audit_user_accounts(device['hostname'], users))
            violations.extend(self.audit_firewall_rules(device['hostname'], firewall_rules))
            
            # Calculate score
            score = self.calculate_security_score(violations)
            
            result = {
                'device': device['hostname'],
                'ip': device['ip'],
                'timestamp': datetime.now().isoformat(),
                'security_score': score,
                'total_violations': len(violations),
                'critical_violations': len([v for v in violations if v['severity'] == 'critical']),
                'warning_violations': len([v for v in violations if v['severity'] == 'warning']),
                'violations': violations
            }
            
            print(f"✓ Audit complete - Security Score: {score}/100")
            print(f"  Found {len(violations)} violations ({result['critical_violations']} critical, {result['warning_violations']} warnings)")
            
            return result
            
        finally:
            ssh_client.close()
    
    def generate_report(self):
        """Generate and display audit report"""
        print(f"\n\n{'#'*60}")
        print(f"# NETWORK SECURITY AUDIT REPORT")
        print(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*60}\n")
        
        for result in self.audit_results:
            if not result:
                continue
                
            print(f"\nDevice: {result['device']} ({result['ip']})")
            print(f"{'─'*60}")
            print(f"Security Score: {result['security_score']}/100")
            print(f"Total Violations: {result['total_violations']}")
            print(f"  - Critical: {result['critical_violations']}")
            print(f"  - Warnings: {result['warning_violations']}")
            
            if result['violations']:
                print(f"\n{'CRITICAL VIOLATIONS':^60}")
                print(f"{'─'*60}")
                critical = [v for v in result['violations'] if v['severity'] == 'critical']
                if critical:
                    for v in critical:
                        print(f"\n✗ {v['rule']}")
                        print(f"  Category: {v['category']}")
                        print(f"  Expected: {v['expected']}")
                        print(f"  Actual: {v['actual']}")
                        print(f"  Remediation: {v['remediation']}")
                else:
                    print("  None")
                
                print(f"\n{'WARNING VIOLATIONS':^60}")
                print(f"{'─'*60}")
                warnings = [v for v in result['violations'] if v['severity'] == 'warning']
                if warnings:
                    for v in warnings:
                        print(f"\n⚠ {v['rule']}")
                        print(f"  Category: {v['category']}")
                        print(f"  Expected: {v['expected']}")
                        print(f"  Actual: {v['actual']}")
                        print(f"  Remediation: {v['remediation']}")
                else:
                    print("  None")
        
        # Save JSON report
        report_file = f"reports/audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.audit_results, f, indent=2)
        
        print(f"\n{'═'*60}")
        print(f"✓ Detailed report saved to: {report_file}")
        print(f"{'═'*60}\n")
    
    def run(self):
        """Execute the complete audit process"""
        print("\n🔒 Network Security Auditor")
        print("="*60)
        
        self.load_inventory()
        self.load_baselines()
        
        for device in self.devices:
            result = self.audit_device(device)
            if result:
                self.audit_results.append(result)
        
        self.generate_report()

def main():
    """Main entry point"""
    # Set up paths
    base_dir = os.path.expanduser('~/network-auditor')
    inventory_file = os.path.join(base_dir, 'device_inventory.yaml')
    baselines_dir = os.path.join(base_dir, 'baselines')
    
    # Create auditor and run
    auditor = NetworkAuditor(inventory_file, baselines_dir)
    auditor.run()

if __name__ == '__main__':
    main()
