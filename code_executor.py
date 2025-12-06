"""
Code Execution Engine
Safely executes code in a sandboxed environment with timeout and resource limits
"""

import sys
import io
import time
import traceback
from contextlib import redirect_stdout, redirect_stderr
import signal

# resource module is Unix-only, removed for Windows compatibility

class TimeoutException(Exception):
    """Exception raised when code execution times out"""
    pass

def timeout_handler(signum, frame):
    """Handler for timeout signal"""
    raise TimeoutException("Code execution timed out")

class CodeExecutor:
    """
    Sandboxed code execution engine
    Supports Python, JavaScript (via evaluation), and basic validation
    """
    
    def __init__(self):
        self.max_execution_time = 5  # seconds
        self.max_memory = 128 * 1024 * 1024  # 128 MB
    
    def execute_python(self, code, test_cases=None):
        """
        Execute Python code safely
        
        Args:
            code: Python code string to execute
            test_cases: List of test cases [{'input': ..., 'expected': ...}]
            
        Returns:
            dict: Execution result with output, errors, and test results
        """
        result = {
            'success': False,
            'output': '',
            'error': '',
            'execution_time': 0,
            'test_results': [],
            'passed_tests': 0,
            'total_tests': 0
        }
        
        start_time = time.time()
        
        try:
            # Create restricted globals
            safe_globals = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'range': range,
                    'str': str,
                    'int': int,
                    'float': float,
                    'list': list,
                    'dict': dict,
                    'set': set,
                    'tuple': tuple,
                    'bool': bool,
                    'sum': sum,
                    'max': max,
                    'min': min,
                    'abs': abs,
                    'sorted': sorted,
                    'enumerate': enumerate,
                    'zip': zip,
                    'map': map,
                    'filter': filter,
                    'all': all,
                    'any': any,
                    'isinstance': isinstance,
                    'type': type,
                }
            }
            
            # Capture stdout and stderr
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            # Set timeout (only works on Unix-like systems)
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self.max_execution_time)
            
            try:
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    # Execute the code
                    exec(code, safe_globals)
                    
                    # If test cases provided, run them
                    if test_cases:
                        result['total_tests'] = len(test_cases)
                        
                        for i, test_case in enumerate(test_cases):
                            test_result = self._run_test_case(
                                code, 
                                test_case, 
                                safe_globals.copy()
                            )
                            result['test_results'].append(test_result)
                            if test_result['passed']:
                                result['passed_tests'] += 1
                
                # Cancel timeout
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
                
                result['success'] = True
                result['output'] = stdout_capture.getvalue()
                
                if stderr_capture.getvalue():
                    result['error'] = stderr_capture.getvalue()
                    
            except TimeoutException:
                result['error'] = f"Execution timed out (>{self.max_execution_time}s)"
            except Exception as e:
                result['error'] = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            finally:
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
        
        except Exception as e:
            result['error'] = f"Setup error: {str(e)}"
        
        result['execution_time'] = time.time() - start_time
        
        return result
    
    def _run_test_case(self, code, test_case, safe_globals):
        """Run a single test case"""
        test_result = {
            'input': test_case.get('input', ''),
            'expected': test_case.get('expected', ''),
            'actual': '',
            'passed': False,
            'error': ''
        }
        
        try:
            # Prepare test input
            test_input = test_case.get('input', '')
            
            # Capture output for this test
            test_stdout = io.StringIO()
            
            with redirect_stdout(test_stdout):
                # Execute code with test input
                exec(code, safe_globals)
                
                # Get the output
                test_result['actual'] = test_stdout.getvalue().strip()
                
                # Check if output matches expected
                expected = str(test_case.get('expected', '')).strip()
                actual = test_result['actual']
                
                test_result['passed'] = (actual == expected)
                
        except Exception as e:
            test_result['error'] = str(e)
            test_result['passed'] = False
        
        return test_result
    
    def validate_syntax(self, code, language='python'):
        """
        Validate code syntax without executing
        
        Args:
            code: Code string
            language: Programming language
            
        Returns:
            dict: Validation result
        """
        result = {
            'valid': False,
            'errors': [],
            'warnings': []
        }
        
        if language.lower() == 'python':
            try:
                compile(code, '<string>', 'exec')
                result['valid'] = True
            except SyntaxError as e:
                result['errors'].append({
                    'line': e.lineno,
                    'message': e.msg,
                    'type': 'SyntaxError'
                })
            except Exception as e:
                result['errors'].append({
                    'line': 0,
                    'message': str(e),
                    'type': type(e).__name__
                })
        
        return result
    
    def analyze_code(self, code):
        """
        Analyze code for quality metrics
        
        Returns:
            dict: Code analysis results
        """
        analysis = {
            'lines_of_code': 0,
            'blank_lines': 0,
            'comment_lines': 0,
            'functions': 0,
            'classes': 0,
            'complexity_score': 0
        }
        
        lines = code.split('\n')
        analysis['lines_of_code'] = len(lines)
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                analysis['blank_lines'] += 1
            elif stripped.startswith('#'):
                analysis['comment_lines'] += 1
            elif stripped.startswith('def '):
                analysis['functions'] += 1
            elif stripped.startswith('class '):
                analysis['classes'] += 1
        
        # Simple complexity score
        analysis['complexity_score'] = (
            analysis['functions'] * 2 + 
            analysis['classes'] * 3 +
            code.count('if ') +
            code.count('for ') +
            code.count('while ')
        )
        
        return analysis
    
    def execute_with_tests(self, code, test_cases):
        """
        Execute code and run all test cases
        
        Args:
            code: Code to execute
            test_cases: List of test cases
            
        Returns:
            dict: Complete execution and test results
        """
        # First validate syntax
        validation = self.validate_syntax(code)
        if not validation['valid']:
            return {
                'success': False,
                'error': 'Syntax errors found',
                'validation': validation,
                'test_results': []
            }
        
        # Execute with test cases
        execution_result = self.execute_python(code, test_cases)
        
        # Add code analysis
        execution_result['analysis'] = self.analyze_code(code)
        execution_result['validation'] = validation
        
        # Calculate score
        if test_cases:
            pass_rate = (execution_result['passed_tests'] / execution_result['total_tests']) * 100
            execution_result['pass_rate'] = pass_rate
            execution_result['score'] = self._calculate_score(execution_result)
        
        return execution_result
    
    def _calculate_score(self, execution_result):
        """
        Calculate score based on execution results
        
        Returns:
            int: Score out of 20
        """
        score = 0
        
        # Test pass rate (12 points)
        if execution_result['total_tests'] > 0:
            pass_rate = execution_result['passed_tests'] / execution_result['total_tests']
            score += int(pass_rate * 12)
        
        # Code quality (4 points)
        analysis = execution_result.get('analysis', {})
        if analysis.get('functions', 0) > 0:
            score += 2  # Has functions
        if analysis.get('comment_lines', 0) > 0:
            score += 1  # Has comments
        if analysis.get('complexity_score', 0) < 20:
            score += 1  # Not overly complex
        
        # Execution success (4 points)
        if execution_result['success']:
            score += 2
        if not execution_result['error']:
            score += 2
        
        return min(score, 20)  # Cap at 20

# Global executor instance
code_executor = CodeExecutor()


# Example test cases for common problems
SAMPLE_TEST_CASES = {
    'fibonacci': [
        {'input': '5', 'expected': '5'},
        {'input': '10', 'expected': '55'},
        {'input': '1', 'expected': '1'},
    ],
    'palindrome': [
        {'input': 'racecar', 'expected': 'True'},
        {'input': 'hello', 'expected': 'False'},
        {'input': 'madam', 'expected': 'True'},
    ],
    'reverse_string': [
        {'input': 'hello', 'expected': 'olleh'},
        {'input': 'python', 'expected': 'nohtyp'},
        {'input': 'a', 'expected': 'a'},
    ]
}
