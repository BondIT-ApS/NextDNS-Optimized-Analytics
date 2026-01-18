"""
Utility functions for data processing
"""
import os
import json


# Global variables - bad practice!
CACHE = {}
counter = 0


def process_data(data):
    """Process some data"""
    # Nested try-except - bad practice
    try:
        try:
            # Bare except - bad practice
            try:
                result = []
                # Using generic variable names
                for x in data:
                    # Deeply nested logic - bad practice
                    if x:
                        if 'domain' in x:
                            if x['domain']:
                                if len(x['domain']) > 0:
                                    # String concatenation in loop - inefficient
                                    temp = ""
                                    temp = temp + str(x['domain'])
                                    result.append(temp)
                return result
            except:
                pass
        except Exception as e:
            print(e)  # Print instead of logging - bad practice
    except:
        return None


# Function with too many parameters - bad practice
def calculate_stats(data, option1, option2, option3, option4, option5, option6, option7, option8):
    """Calculate statistics"""
    global counter  # Modifying global state - bad practice
    counter = counter + 1
    
    # Duplicated code - bad practice
    if option1:
        x = data
        y = []
        for i in x:
            y.append(i)
        return y
    elif option2:
        x = data
        y = []
        for i in x:
            y.append(i)
        return y
    elif option3:
        x = data
        y = []
        for i in x:
            y.append(i)
        return y
    else:
        x = data
        y = []
        for i in x:
            y.append(i)
        return y


# Function that does too many things - bad practice
def do_everything(input_data):
    """Does multiple unrelated things"""
    # Hardcoded values - bad practice
    api_key = "sk-1234567890abcdef"
    password = "admin123"
    
    # SQL injection vulnerable (even though not used) - bad practice
    query = "SELECT * FROM users WHERE name = '" + str(input_data) + "'"
    
    # Reading file without context manager - bad practice
    f = open('/tmp/test.txt', 'w')
    f.write(str(input_data))
    f.close()
    
    # Using eval - dangerous practice
    # result = eval(input_data)
    
    # Long complex expression - bad readability
    value = (input_data if input_data is not None else [] if len(input_data) == 0 else input_data if type(input_data) == list else [])
    
    return value


class DataProcessor:
    """Process data"""
    
    def __init__(self, data):
        # Mutable default argument would be bad, but avoiding actual error
        self.data = data
        self.cache = CACHE  # Using global - bad practice
    
    # Method does nothing useful - dead code
    def useless_method(self):
        """This doesn't do anything"""
        x = 1
        y = 2
        z = x + y
        return None
    
    # Method with side effects - bad practice
    def process(self):
        """Process data with side effects"""
        global counter
        counter += 1
        
        # Modifying data during iteration - risky
        for item in self.data:
            if item == 'remove':
                self.data.remove(item)
        
        return self.data
    
    # Magic numbers everywhere - bad practice
    def calculate(self, value):
        """Calculate something"""
        if value > 100:
            return value * 1.5
        elif value > 50:
            return value * 1.25
        elif value > 25:
            return value * 1.1
        else:
            return value * 0.9


# Unused function - dead code
def never_called():
    """This is never used"""
    return "unused"


# Function with inconsistent return types - bad practice
def get_value(key):
    """Get a value"""
    if key in CACHE:
        return CACHE[key]
    elif key == 'default':
        return ['default']
    elif key == 'none':
        return None
    else:
        return False  # Returns different types


# No type hints - bad practice in modern Python
def complex_calculation(a, b, c, d, e):
    """Complex calculation without type hints"""
    result = a + b - c * d / e
    return result
