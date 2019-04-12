#!/usr/bin/python
# -*- coding: UTF-8 -*-

import xml.dom.minidom
import json
import requests
import argparse
import os.path

TestCase_content = {
       "case_id": "13283",
       "case_name": "Java GUI test case", #Optional, nice to have
       "case_detail": "Test only",        #Optional, nice to have
       "case_component": "MC",            #MC/Server/DPE/DTLT/VCP/…
       "case_product": "Avamar",          #Avamar/Networker/…
       "case_project": "Rooster",         #Rooster/Kensington/…
       "case_result": "PASS",             #PASS/FAIL/SKIPPED/…
       "case_link": "",                   #Optional
       "case_type": "New Feature ",       #New Feature/Legacy/SecurityRollup               
       "test_type": "Daily",              #Daily/Smoke/Regression/…
       "test_tag": "Java GUI",            #Optional, /Windows/Linux/anything/… used for search by filter
       "test_build": "7.6.0.33",          #DPE or VCP or Avamar build
       "security_build": "",              #Optional, Security build number
       "start_time": "",                  #Optional, format should be timestamp
       "end_time": "",                    #Optional, format should be timestamp
       "duration": "",                    #Optional, seconds
       "log": "test log"                  #Optional
}

               
Summary_report = {

       "case_component": "MC",                            #MC/DPE/VCP/DTLT/...
       "case_product": "Avamar",                          #Avamar/Networker
       "case_project": "Rooster",                         #Rooster/Kensington/Bootes M2/…
       "test_type": "Daily",                              #Daily/Smoke/Regression/Quartly/…
       "test_build": "7.6.0.33",                          #DPE or VCP or Avamar build
       "security_build": "",                              #Optional, Security build
       "detail_link": "http://taas.datadomain.com/",      #Detail link
       "send_summary":"NO"                                #YES/NO, default is NO
}

test_status = {
        "PASS":   "1",
        "FAILED": "5"
}

report_cases   = 'http://10.98.138.179/result/case/'
report_summary = 'http://10.98.138.179/result/summary/'
# Main
def main():

    parser = argparse.ArgumentParser(prog='parse_xml.py',
                                     usage='%(prog)s -b <build> xml_file',
                                     description='%(prog)s is the test log uploader for robot output.xml',
                                     version='Version 1.0')
    parser.add_argument("-b", "--build", dest="build", type=str, help="Test build version")
    parser.add_argument("-p", "--project", dest="project", type=str, help="build project name")
    parser.add_argument("-t", "--type", dest="type", type=str, help="project type", default="Legacy")
    parser.add_argument("-l", "--summary_link", dest="summary_link", type=str, help="summary link", default="https://10.110.203.27/view/MC-CI/job/Main-CI-Rooster-JavaGUI/")
    parser.add_argument(dest="xml_file", type=str, help="Test report xml file")
    args = parser.parse_args()
    
    if not args.build:
        print "Need providing build number\n  Usage: ",parser.usage
        return False
    Summary_report["test_build"]   = args.build
    TestCase_content["test_build"] = args.build
    Summary_report["case_project"]   = args.project
    TestCase_content["case_project"] = args.project
    TestCase_content["case_type"] = args.type
    Summary_report["detail_link"]   = args.summary_link
    if not os.path.isfile(args.xml_file):
        print "Not find the report xml file."
        return False
    # open xml with minidom
    DOMTree = xml.dom.minidom.parse(args.xml_file)
    collection = DOMTree.documentElement

    # get all test cases
    print collection.localName
    #
    projects = getChildNodes(collection,"project")
    project = projects[0]
    print "Now we get project: ",getText(getChildNodes(project,"name")[0])
    test_suites = getChildNodes(project,"testsuite")
    test_suite  = test_suites[0]
    
    test_suite_name = getChildNodes(test_suite,"name")[0]
    print getText(test_suite_name)
    #print test_suite_name.nodeValue
    test_run = getChildNodes(test_suite,"test-run")[0]
    test_cases = getChildNodes(test_run,"testcase")
 
    for case in test_cases:
        print "*****case*****"
        case_id   = getChildNodes(case,"name")[0]
        case_id   = getText(case_id)
        case_name = case_id
        if len(getChildNodes(case,"comment"))==1:
            comment   = getChildNodes(case,"comment")[0]
            #print "comment:",comment.toxml()
            comment   = getChildNodes(comment,"name")[0]
            #comment   = getText(comment.childNodes[0])
            print "case name: ",comment.firstChild.wholeText
            case_name = comment.firstChild.wholeText
        TestCase_content["case_id"]   = case_id
        TestCase_content["case_name"] = case_name
        status = getChildNodes(case,"status")[0]
        status = getText(status)
        print status
        if status == test_status["PASS"]:
            print "pass"
            TestCase_content["case_result"] = "PASS"
        else:
            TestCase_content["case_result"] = "FAIL"
        #continue

        print TestCase_content
        json_data = json.dumps(TestCase_content)
        
        try:
            print "Parser: Post Data to %s" % (report_cases,)
            r = requests.post(report_cases, json_data, timeout=10)
            print "Connected to %s with code %s" % (report_cases, r,)
        except requests.exceptions.Timeout:
            print "Timeout occurred. Retry.."
        except requests.exceptions.ConnectionError:
            print "Connection Error. Return"
            return False
    
    #Summary_report["detail_link"] = "https://10.110.203.27/view/MC-CI/job/Main-CI-Rooster-JavaGUI/"
    print Summary_report
    json_data = json.dumps(Summary_report)
    try:
        print "Parser: Post Summary_report to %s" % (report_summary,)
        r = requests.post(report_summary, json_data, timeout=10)
        print "Connected to %s with code %s" % (report_summary, r,)
    except requests.exceptions.Timeout:
        print "Timeout occurred. Retry.."
    except requests.exceptions.ConnectionError:
        print "Connection Error. Return"
        return False
    
def getText(node):
    rc = []
    nodeList = node.childNodes
    for node in nodeList:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)
            
def getChildNodes(parentNode,nodeName):
    nodes = []
    for node in parentNode.childNodes:
        if node.localName == nodeName:
            nodes.append(node)
    return nodes
    
if __name__ == "__main__":
    main()
