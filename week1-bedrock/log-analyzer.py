# Kubernetes Pod log Analyzer using AWS Bedrock
# Week 1 - AI in DevOps learning project

# Real-World use case: Automatically analyze pod crash logs during incidents 
# instead of engineers manually reading hundreds of lines at 2am.

# Author: Sohel Mujawar

import boto3
import json
import sys
import os
from datetime import datetime

def read_log_file(filepath):
    """
    Read log file from disk.
    In production this would come from:
    - kubectl logs <pod-name> piped to this script
    - Loki API query
    - CloudWatch logs
    """

    if not os.path.exists(filepath):
        print(f"ERROR: Log file not found: {filepath}")
        sys.exit(1)

    with open(filepath, 'r') as f:
        return f.read()
    
def analyze_log_with_bedrock(log_content, service_name="unknown-service"):
    """
    Send log content to Claude on AWS Bedrock for intelligent analysis.
    Why Claude Haiku?
        - Fastest response time (imp during incidents)
        - Cheapest model (~$0.00025 per 1k input tokens)
        - more than capable for log analysis tasks
        - A 500-line log = roughly 2000 tokens = less than $0.001 per analysis
    """

    #Initialize Bedrock client 
    # boto3 automatically uses credentials from ~/.aws/credentials
    bedrock = boto3.client(
        service_name='bedrock-runtime',
        region_name= 'ap-south-1'
    )

    # This is called a "prompt"
    prompt = f"""You are an expert Site Reliability Engineer (SRE) analyzing kubernetes pod logs.
                Service name: {service_name}
                Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                Here are the pod logs to analyze:
                <logs>
                {log_content}
                </logs>

                Provide a strucured incident analysis with exactly these sections:
                **SEVERITY:** [CRITICAL / HIGH / MEDIUM / LOW]

                **ROOT CAUSE:**
                One clear sentence explaining the exact technical reason the failed.

                **WHAT HAPPENED:**
                2-3 sentences explaining the sequence of events in plain English.

                **IMMEDIATE FIX:**
                Step-by-step commands an engineer should run right now to resolve this.

                **PREVENTION:**
                What should be changes in the deployment/config to prevent this happening again.

                **RELATED COMPONENTS TO CHECK:**
                List other services or infrastructure that might be affected.

                Be direct and technical. No fluff, And engineer is reading this at 2am during and incident.
            """
    
    # Call Claude Haiku via Bedrock
    #This is the "Messages API" format same as Anthropic's direct API
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        })
    )

    #parse the response
    response_body = json.loads(response['body'].read())
    analysis = response_body['content'][0]['text']

    return analysis

def print_report(analysis, log_file, service_name):
    """Print formatted incident report to terminal."""

    print("\n" + "=" * 60)
    print("AI_POWERED INCIDENT ANALYSIS REPORT")
    print("\n" + "=" * 60)
    print(f"Log file: {log_file}")
    print(f"Service: {service_name}")
    print(f"Analyzed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Powered by: AWS Bedrock (Claude Haiku)")
    print("\n" + "=" * 60)
    print()
    print(analysis)
    print()
    print("\n" + "=" * 60)
    print("END OF REPORT")
    print("\n" + "=" * 60)

def save_report(analysis, log_file, service_name):
    """
    Save report to file.
    In production: this would POST to PagerDuty, Slack or JIRA auttomatically.
    """

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    report_file = f"incident-report-{service_name}-{timestamp}.txt"

    with open(report_file, 'w') as f:
        f.write(f"Incident Report - {service_name}\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"Source log: {log_file}\n")
        f.write("="*60 + "\n\n")
        f.write(analysis)

    print(f"Report saved: {report_file}")
    return report_file

def main():
    # Get log file path from command line argument
    if len(sys.argv) < 2:
        print("Usage: python3 log-analyzer.py <log-file> [service-name]")
        print("Example: python3 log-analyzer.py sample-pod-log.txt order-service")
        sys.exit(1)

    log_file = sys.argv[1]
    service_name = sys.argv[2] if len(sys.argv) > 2 else "unknown-service"

    print(f"\n Analyzing logs for: {service_name}")
    print(f"\n Reading log file: {log_file}")
    print("Sending to AWS Bedrock (Claude Haiku)...")
    print("This takes 3-8 seconds...\n")

    #Read the log
    log_content = read_log_file(log_file)

    #Analyze with AI
    analysis = analyze_log_with_bedrock(log_content, service_name)

    #print to terminal
    print_report(analysis, log_file, service_name)

    #save to file
    save_report(analysis, log_file, service_name)

if __name__ == "__main__":
    main()

