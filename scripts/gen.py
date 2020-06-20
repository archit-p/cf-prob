import requests
import json
import os
import time

def request_cf(method, payload, auth_key):
    if auth_key == None:
        r = requests.get("http://codeforces.com/api/" + method, params=payload)
        if r.status_code != 200:
            print("Didn't receive response")
            return None
        resp = json.loads(r.text)
        if resp["status"] != "OK":
            print("Error in API method")
            return None
        return resp["result"]

def load_from_file(filename):
    if not os.path.isfile(filename):
        return None
    f = open(filename, "r")
    data = json.loads(f.read())
    f.close()
    if int(time.time()) - int(data["creation_time"]) >= 24 * 60 * 60:
        return None
    return data["data"]

def save_to_file(filename, data):
    f = open(filename, "w")
    f.write(json.dumps({"creation_time" : int(time.time()), "data" : data}))
    f.close()

def get_cf_contests_after(cid):
    contests = load_from_file("contests.list")
    if contests == None:
        contests = request_cf("contest.list", None, None)
        save_to_file("contests.list", contests)

    cf_contests = [x for x in contests if (x["type"] == "CF" and (("Div. 1" in x["name"] or "Div. 2" in x["name"])) or
                    (x["type"] == "ICPC" and "Div. 3" in x["name"])) and
                    x["phase"] == "FINISHED" and
                    x["id"] > cid]
    return cf_contests

def get_problems():
    problems = load_from_file("problems.list")
    if problems == None:
        problems = request_cf("problemset.problems", None, None)
        save_to_file("problems.list", problems)
    return problems

def get_division(contest_name):
    if "Div. 1" in contest_name:
        return 1
    elif "Div. 2" in contest_name:
        return 2
    elif "Div. 3" in contest_name:
        return 3
    else:
        return 4

def filter_problems(contests, problems, cid):
    contests_dict = dict()
    for contest in contests:
        contests_dict[contest["id"]] = contest["name"]

    filtered_problems = dict()
    for problem, problem_stat in zip(problems["problems"], problems["problemStatistics"]):
        try:
            if problem["contestId"] in contests_dict.keys() and problem["rating"] is not None:
                div = get_division(contests_dict[problem["contestId"]])
                ptype = problem["index"]
                if len(ptype) == 2:
                    ptype = ptype[:1]
                if ptype > 'E':
                    continue
                ind = "Div. " + str(div) + "/" + ptype
                if not ind in filtered_problems.keys():
                    filtered_problems[ind] = []
                filtered_problems[ind].append((problem, problem_stat))
        except:
            print("Couldn't load problem " + str(problem["contestId"]) + problem["index"])
    return filtered_problems

def get_submissions(handle):
    def load_one_more(fr=1):
        return request_cf("user.status", {"handle" : handle, "from" : fr}, None)[0]
    submissions = load_from_file(handle + ".submissions")
    if submissions == None:
        submissions = request_cf("user.status", {"handle" : handle}, None)
    last_id = submissions[0]["id"]
    fr = 1
    submission = load_one_more(fr)
    while submission["id"] != last_id:
        submissions = [submission] + submissions
        fr += 1
        submission = load_one_more(fr)
    save_to_file(handle + ".submissions", submissions)
    return submissions

def get_problems_status(submissions):
    problems_status = dict()
    for submission in submissions:
        ptype = submission["problem"]["index"]
        if len(ptype) == 2:
            ptype = ptype[:1]
        problem_ind = str(submission["problem"]["contestId"]) + ptype
        verdict = submission["verdict"]
        if problem_ind in problems_status.keys():
            if problems_status[problem_ind] != "Yes" and verdict == "OK":
                problems_status[problem_ind] = "Yes"
        else:
            if verdict == "OK":
                problems_status[problem_ind] = "Yes"
            else:
                problems_status[problem_ind] = ""
    return problems_status

def get_problem_url(problem):
    return "http://codeforces.com/problemset/problem/" + \
            str(problem["contestId"]) + "/" + problem["index"]

def get_status_url(problem):
    return "http://codeforces.com/problemset/status/" + \
            str(problem["contestId"]) + "/problem/" + problem["index"]

def get_file_name(problem_type):
    problem_file_name = ''.join(e for e in problem_type if e.isalnum())
    problem_file_name = problem_file_name.lower()
    return problem_file_name[:4] + '/' + problem_file_name[4:] + '.md'

cid = 600
print("Loading contests after #" + str(cid) + "...")
contests = get_cf_contests_after(cid)
print("OK")

print("Loading problems...")
problems = get_problems()
filtered_problems = filter_problems(contests, problems, cid)
print("OK")

for problem_type in sorted(filtered_problems.keys()):
    print(problem_type, len(filtered_problems[problem_type]), " problems loaded")

handle = "archit-p"
print("Loading submissions for handle ", handle, "...")
submissions = get_submissions(handle)
problems_status = get_problems_status(submissions)
print("OK")

print("Generating markdown...")
for problem_type in sorted(filtered_problems.keys()):
    md = open(get_file_name(problem_type), 'w')
    md.write("No.|Index|Name|Rating|Status\n:-:|:-:|:-:|:-:|:-:\n")
    md.close()
    md = open(get_file_name(problem_type), 'ab')
    idx = 1
    for problem, problem_stat in sorted(filtered_problems[problem_type],
                                        key=lambda x: (x[0]["rating"], -x[1]["solvedCount"])):
        ptype = problem["index"]
        problem_ind = str(problem["contestId"]) + ptype
        if len(ptype) == 2:
            ptype = ptype[:1]
        if problem_ind in problems_status:
            status = problems_status[problem_ind]
        else:
            status = ""
        problem_row = str(idx)
        problem_row += "|[" + str(problem["contestId"]) + str(ptype) + "](" + get_problem_url(problem) + ")"
        problem_row += "|[" + problem["name"] + "](" + get_problem_url(problem) + ")"
        problem_row += "|" + str(problem["rating"])
        problem_row += "|" + status + "\n"
        md.write(problem_row.encode("UTF-8"))
        idx += 1

    md.close()
