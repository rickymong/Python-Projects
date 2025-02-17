import random 

def question():
    operators = ["+", "-", "*"]
    operator = random.choice(operators)

    if operator == "+":
        num1 = random.randint(1, 100)
        num2 = random.randint(1,100)
        equation = str(num1) + operator + str(num2)
        return equation 
    elif operator == "-":
        num1= random.randint(1, 100)
        num2 = random.randint(1, 100)
        equation = str(num1) + operator + str(num2)
        return equation 
    elif operator == "*":
        num1 = random.randint(1, 10)
        num2 = random.randint(1,10)
        equation = str(num1) + operator + str(num2)
        return equation 
def getanswer(question):
    answer = eval(question)
    return answer

import time
score = 0
start = time.time()
for i in range(10):
    q = question()
    print("Question", i+1,":")
    print(q)
    answer = input("Enter your answer: ")
    if answer.isnumeric():
        if int(answer) == getanswer(q):
            score = score + 4
        else: 
            score -= 1
    elif answer == "":
        score += 0
    else:
        print("Invalid input. No changes made to score.")
end = time.time()
time_taken = end - start
minutes = int(time_taken/60)
seconds = int(time_taken%60)
print("Your score is:", score, "/40")
print("Time taken:", minutes, "minutes and", seconds, "seconds")