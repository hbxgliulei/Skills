# -*- coding: utf-8 -*-
"""Batch fetch 人民日报 for a date range, one MD file per day.

Usage: python batch_fetch.py YYYY-MM-DD YYYY-MM-DD
Invokes fetch_rmrb.py for each date, verifies the output file
(>=1 section, >=1 article), retries up to 3 times on failure.
"""
import subprocess, sys, os, re, datetime, time

def main():
    start = datetime.date.fromisoformat(sys.argv[1])
    end = datetime.date.fromisoformat(sys.argv[2])
    here = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(here, "fetch_rmrb.py")

    d = start
    while d <= end:
        ds = d.strftime("%Y-%m-%d")
        fpath = os.path.join(here, "人民日报_%s.md" % ds)
        # 断点续传：已有且有效的文件直接跳过
        if os.path.exists(fpath):
            txt = open(fpath, encoding="utf-8").read()
            nsec = len(re.findall(r"^## 第\d+版", txt, re.M))
            nart = len(re.findall(r"^### \d+\.", txt, re.M))
            if nsec >= 1 and nart >= 1:
                print("RESULT %s SKIP(已有) sec=%d art=%d" % (ds, nsec, nart), flush=True)
                d += datetime.timedelta(days=1)
                continue
        status = "FAIL"
        nsec = nart = 0
        for attempt in range(1, 4):
            r = subprocess.run([sys.executable, script, ds],
                               capture_output=True, text=True, timeout=900)
            if os.path.exists(fpath):
                txt = open(fpath, encoding="utf-8").read()
                nsec = len(re.findall(r"^## 第\d+版", txt, re.M))
                nart = len(re.findall(r"^### \d+\.", txt, re.M))
                if nsec >= 1 and nart >= 1:
                    status = "OK"
                    break
            print("%s attempt=%d %s sec=%d art=%d" % (ds, attempt, status, nsec, nart), flush=True)
            time.sleep(8)
        print("RESULT %s %s sec=%d art=%d" % (ds, status, nsec, nart), flush=True)
        d += datetime.timedelta(days=1)

if __name__ == "__main__":
    main()
