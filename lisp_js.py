# Scheme interpreter written in Python
""" program --> Parser --> representation --> Execution --> output """

"""          Symbol, Env classes           """

import json

class Env(dict):
    # Env is a subclass of dict.
    # An environment is a dictionary of {'var': val} pairs with an outer Env.
    def __init__(self, parms=(), args=(), outer=None):
        self.update(zip(parms, args))
        self.outer = outer
    def find(self, var):
        # Find the innermost Env where var appears.
        # Env.find finds the right environment according to lexical scoping rules.

        # return self if var in self else self.outer.find(var)
        if var in self:
            return self
        else: 
            return self.outer.find(var)

def add_globals(env):
    # Add Scheme standard procedures to an environment. This is only called once at the start of the program.
    import operator as op
    import arithmetic as art

    env.update({
            # art file allows for *args
            '+' : art.add, 
            '-' : art.sub, 
            '*' : art.mul, 
            '/' : art.div, 
            'not' : op.not_,
            '>' : op.gt,
            '<' : op.lt,
            '>=' : op.ge,
            '<=' : op.le,
            '=' : op.eq,
            'equal?' : op.eq, # true if variable values are equal
            'eq?' : op.is_, # true if variables point to the same object in memory
            'length' : len,
            'cons' : lambda x, y : [x] + y, # what the shit is this
            'car' : lambda x : x[0],
            'cdr' : lambda x : x[1:],
            'append' : op.add, # this works for Scheme, I guess? 
            # Well, Python concatenates strings this way...
            'list' : lambda *x : list(x),
            # list() -> new empty list
            # list(iterable) -> new list initialized from iterable's items
            # syntactic sugar. l = [] is the same as l = list()
            'list?' : lambda x : isa(x, list),
            'null?' : lambda x : x == [],
            'symbol?' : lambda x : isa(x, Symbol)    
        })
    return env

global_env = add_globals(Env())

"""          eval           """

# Evaluate an expression x in an environment env.
# x is a list
def eval(x, env=global_env):
    print """


    """
    
    # variable reference
    # if x is a str
    if isa(x, Symbol):
        print '%r is a Symbol ' % x,
        print 'that evaluates to %r' % env.find(x)[x]
        # .find is a method defined in the Env class
        # env.find locates the proper environment
        # the [x] returns the actual procedure/symbol definition
        return env.find(x)[x]
         
    # constant literal
    elif not isa(x, list):
        # print "%r is not a list; %r is of type %r" % (x, x, type(x))
        return x

    # (quote exp)
    elif x[0] == 'quote':
        print 'quote'
        (_, exp) = x # _ is a character we use as a variable.
        return exp

    # conditional (if test conseq alt)
    elif x[0] == 'if':
        (_, test, conseq, alt) = x
        print 'if %r then %r else %r' % (test, conseq, alt)

        if_statement = eval(test, env)
        if_eval = True if eval(test, env) else False

        print 'the if evaluates to %r, which is %r' % (if_statement, if_eval) 
        return eval((conseq if eval(test, env) else alt), env)
        # value_when_true if condition else value_when_false

    # assignment (set! var exp)
    elif x[0] == 'set!':
        (_, var, exp) = x
        env.find(var)[var] = eval(exp, env) # recursively eval the expression

    # (define var exp)
    elif x[0] == 'define':
        (_, var, exp) = x
        print 'define %r as %r' % (var, exp)
        env[var] = eval(exp, env) # adds var to the global environment dictionary

    # procedure (lambda (var*) exp)
    elif x[0] == 'lambda':
        print '%r is a lambda procedure' % x
        (_, vars, exp) = x
        print 'vars', vars
        print 'exp', exp
        return lambda *args: eval(exp, Env(parms=vars, args=args, outer=env))

    # sequencing (begin exp*)
    elif x[0] == 'begin':
        for exp in x[1:]:
            val = eval(exp, env)
        return val # val will keep being reassigned, so we only return the last val?

    else:
        print 'procedure call!'
        # procedure call (proc exp*)
        exps = [eval(exp, env) for exp in x] # list of evaluated exp
        proc = exps.pop(0) # procedure is the first element of exps, (* 9 9)
        
        # print proc([9, 8, 7]) # doesn't work
        # print proc(9, 8, 7)
        # # * turns a series of args into an iterable (list) as it passes into a function

        return proc(*exps) # arbitrary amount of exps, which will be recursively evaluated
        # final returned value is the final value...of course

# alias
isa = isinstance # isinstance(9, int) --> True, isinstance(9, str) --> False
Symbol = str

"""          parse, read, user interaction           """

# Parsing is traditionally separated into two parts: lexical analysis, 
# in which the input character string is broken up into a sequence of tokens, 
# and syntactic analysis, in which the tokens are assembled into an internal representation. 
# The Lispy tokens are parentheses, symbols (such as set! or x), and numbers (such as 2).

def parse(s):
    # read a Scheme expression from a string
    return read_from(tokenize(s))

def tokenize(s):
    # convert a string into a list of tokens
    # add white space in between parentheses and split on white space
    return s.replace('(', ' ( ').replace(')', ' ) ').split()

def read_from(tokens):
    # read an expression from a sequence of tokens
    # print 'reading from tokens %r' % tokens
    if len(tokens) == 0:
        raise SyntaxError('unexpected EOF while reading')
    token = tokens.pop(0) # pop off first token and assign to token for analysis

    # need to save leading symbol for new node -- will use for expression_trace
    new_node_leading_symbol = tokens[0]

    if '(' == token:

        # print '\n\nSTARTING A NEW NODE.'
        # each node has its own environment -- must account for this later in eval
        # could optimize this later to refer to later constructed nodes. Meh. 

        expression_tokens = []
        while tokens[0] != ')':
            expression_tokens.append(read_from(tokens))

        # print 'popping off', tokens[0]
        tokens.pop(0) # pop off ')' Popping is faster than deleting. What. 

        # need to only append complete expression onto expression_trace
        # when tokens == [], complete expression has been traced
        # append to expression_trace
        if not tokens:
            new_node = {new_node_leading_symbol : expression_tokens}
            expression_trace.append(new_node)

        # print 'returning expression tokens %r' % expression_tokens
        # Holy shit, these are lists within lists. Awesome. 
        # It's the binary tree! :O 
        return expression_tokens

    # account for '()'
    elif ')' == token:
        raise SyntaxError('unexpected token )')

    else:
        return atom(token)

def atom(token):
    # numbers become numbers
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        # every other token is a symbol
        except ValueError:
            return Symbol(token)

def to_string(exp):
    # convert Python object back into Lisp-readable string
    if isa(exp, list):
        # print 'to_string on a list %r' % exp
        return '(' + ' '.join(map(to_string, exp)) + ')'
    else:
        # print 'to_string on a non-list %r' % exp
        return str(exp) # called via the map function above. fancy. 3/12 - what was I talking about...
        # can simply write .join(map(str(exp), exp)) above? 

def to_js(exp):
    
    print '\n\nexp is now', exp
    if exp == None: 
        return ''
    if type(exp) == int or type(exp) == float or type(exp) == str:
        return str(exp)

    token = exp.pop(0)
    print 'THE TOKEN IS ', token

    # ['define', 'area', ['lambda', ['r'], ['*', 3.141592653, ['*', 'r', 'r']]]]
    # (define fact (lambda (n) (if (<= n 1) 1 (* n (fact (- n 1))))))

    if token == 'define':
        var_name = exp[0]
        value = exp[1]
        if value[0] == 'lambda':
            args = value[1]
            
            if len(args) == 1:
                args = args[0] # should already be a string
            else: 
                args = ', '.join(args)
                print args

            if global_env.get(value[2][0]):
                return_statement = 'return '
            else: 
                return_statement = '' 
            return 'var ' + var_name + ' = function(' + args +') { ' + return_statement + to_js(value[2]) + ' }'
        else: 
            return value

    if token == 'if':
        test = exp[0]
        conseq = exp[1]
        alt = exp[2]

        return 'if ' + to_js(test) + ' { return ' + to_js(conseq) + ' } else { return ' + to_js(alt) + ' }'

    if type(token) != int:
        # MUST DEAL WITH THIS - must account for user-defined variables in global_env

            # '+' : art.add, 
            # '-' : art.sub, 
            # '*' : art.mul, 
            # '/' : art.div, 
            # 'not' : op.not_,
            # '>' : op.gt,
            # '<' : op.lt,
            # '>=' : op.ge,
            # '<=' : op.le,


# (define count (lambda (item L) (if L (+ (equal? item (car L)) (count item (cdr L))) 0)))

        # if global_env[token]:
        if token in ['+', '-', '*', '/', '>', '<', '>=', '<=']:
            print 'THIS IS A THING', token
            s = '(' + to_js(exp[0])
            for i in exp[1:]:
                s += ' ' + token + ' ' + to_js(i)
            return s + ')'
        # elif token in ['equal?', 'eq?', 'list?', 'null?', 'symbol?']:
        #     s = '(' + to_js(exp[0])

        elif token == 'equal?':
            arg1 = exp[0]
            arg2 = exp[1]
            print arg1, 'and', arg2
            s = to_js(arg1) + ' == ' + to_js(arg2)
            return s

        else:
            print 'fact exp is', exp
            # function call situation
            return token + to_js(exp[0])
    else:
        # print 'returning a string', token
        print type(str(token))
        return str(token) + to_js(exp)




def repl():
    # prompt-read-eval-print loop

    while True:
        user_input = raw_input('lis.py > ')
        # able to push enter infinitely
        if user_input:
            # return_json(user_input)
            val = eval(parse(user_input))
            # js = to_js(parse(user_input))
            # print 'exp parsed', parse(user_input)
            # print 'JavaScript, yo!--  ', js
            if val:
                print to_string(val)


def main():
    """In case we need this for something"""
    pass

if __name__ == "__main__":
    global expression_trace
    expression_trace = []

    user_input ='(* 93 8 (+ 9 9 4)9 (- 0 9 8))'
    # user_input = '(+ 9 0 8 0)'
    # user_input = '(define area (lambda (r) (* 3.141592653 r r)))'
    user_input = '(define fact (lambda (n) (if (<= n 1) 1 (* n (fact (- n 1))))))'
    user_input = '(define count (lambda (item L) (if L (+ (equal? item (car L)) (count item (cdr L))) 0)))'
    user_input = '(define fib (lambda (n) (if (< n 2) n (+ (fib (- n 1)) (fib (- n 2))))))'

    l = parse(user_input)
    print 'evaluates to', eval(l)
    print 'exp parsed', l
    js = to_js(l)
    print 'JavaScript, yo!--  ', js


    # uncomment repl() for troubleshooting in the terminal
    # repl()
