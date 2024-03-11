# Updated function to check specific conditions

def check_logs(algo,logs):
    for log in logs:
        try:
        # Direct numerical comparison
            if log["first_executed_time"] < log["arrival_time"] :
                print(log)
                return False
            if not log["ifdone"]:
               print(log["ifdone"])
               return False
        except Exception as e:
            # If there's an error in parsing or condition checking, consider it as failure
            return str(algo)+" "+str(e)
    return True

