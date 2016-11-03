#@+leo-ver=5-thin
#@+node:ekr.20161029103517.1: * @file importers/python.py
'''The new, line-based, @auto importer for Python.'''
import leo.core.leoGlobals as g
import leo.plugins.importers.basescanner as basescanner
import re
#@+<< python: new_scanner >>
#@+node:ekr.20161103070215.1: ** << python: new_scanner >>
new_scanner = False
#@-<< python: new_scanner >>
#@+others
#@+node:ekr.20161029103640.1: ** class PythonLineScanner
class PythonLineScanner(basescanner.BaseLineScanner):
    '''A scanner for the perl language.'''
    
    def __init__(self, importCommands, atAuto,language=None, alternate_language=None):
        '''The ctor for the PythonScanner class.'''
        c = importCommands.c
        ###clean = c.config.getBool('python_importer_clean_lws', default=False)
        # Init the base class.
        basescanner.BaseLineScanner.__init__(self, importCommands,
            atAuto = atAuto,
            gen_clean = False, # True: clean blank lines & unindent blocks.
            gen_refs = False, # Don't generate section references.
            language = 'python', # For @language.
            state = PythonScanState(c),
            strict = True, # True: leave leading whitespace alone.
            ############ Customize rescan blocks ###########
        )
        
    #@+others
    #@+node:ekr.20161029103640.2: *3* python.clean_headline
    def clean_headline(self, s):
        '''Return a cleaned up headline s.'''
        m = re.match(r'\s*def\s+(\w+)', s)
        if m:
            return m.group(1)
        else:
            m = re.match(r'\s*class\s+(\w+)', s)
            if m:
                return 'class %s' % m.group(1)
            else:
                return s.strip()
    #@+node:ekr.20161029103640.3: *3* python.clean_nodes
    def clean_nodes(self, parent):
        '''Clean nodes as part of the post pass.'''
        # Move trailing comments into following def nodes.
        for p in parent.subtree():
            next = p.threadNext()
            lines = g.splitLines(p.b)
            if lines and next:
                while lines and lines[-1].strip().startswith('#'):
                    next.b = lines.pop() + next.b
                p.b = ''.join(lines)
    #@-others
#@+node:ekr.20161029103615.1: ** class PythonScanState
class PythonScanState:
    '''A class to store and update scanning state.'''
    
    def __init__(self, c):
        '''Ctor for the PythonScanState class.'''
        self.tab_width = c.tab_width
        self.base_indent, self.indent = 0, 0
        self.context = '' # Represents cross-line constructs.
        self.is_class_or_def = False
        self.stack = []

    #@+others
    #@+node:ekr.20161029103952.2: *3* python_state.__repr__ & __str__
    def __repr__(self):
        return 'PythonScanState: base indent: %2d indent: %2d context: %2r' % (
            self.base_indent, self.indent, self.context)

    __str__ = __repr__
    #@+node:ekr.20161029103952.3: *3* python_state.continues_block and starts_block
    def continues_block(self):
        '''Return True if the just-scanned lines should be placed in the block.'''
        if self.context: ###  or not self.is_class_or_def:
            return True
        else:
            return self.indent > self.base_indent

    def starts_block(self):
        '''Return True if the just-scanned line starts an inner block.'''
        if self.context: ### or not self.is_class_or_def:
            return False
        else:
            ### return self.indent >= self.base_indent
            return self.is_class_or_def and self.indent >= self.base_indent
    #@+node:ekr.20161029103952.5: *3* python_state.clear, push & pop
    def clear(self):
        '''Clear the state.'''
        self.base_indent = self.indent = 0
        self.context = '' 

    def pop(self):
        '''Restore the base state from the stack.'''
        self.base_indent = self.stack.pop()
        
    def push(self):
        '''Save the base state on the stack and enter a new base state.'''
        self.stack.append(self.base_indent)
        self.base_indent = self.indent
    #@+node:ekr.20161029103615.2: *3* python_state.scan_line
    def scan_line(self, s):
        '''Update the scan state by scanning s.'''
        #pylint: disable=arguments-differ
        trace = False and not g.unitTesting
        
        def match(i, pattern):
            return pattern and g.match_word(s, i, pattern)

        if self.context == 'bs-nl':
            self.is_class_or_def = False
            self.context = ''
        else:
            lws_i = g.skip_ws(s, 0)
            self.is_class_or_def = match(lws_i, 'class') or match(lws_i, 'def')
            self.indent = g.computeLeadingWhitespaceWidth(s, self.tab_width)
        contexts = ['', '"""', "'''", '"', "'"]
        assert self.context in contexts, repr(self.context)
        i = 0
        while i < len(s):
            progress = i
            ch = s[i]
            if self.context:
                if ch == '\\':
                    i += 1 # Eat the *next* character too.
                elif self.context == ch:
                    self.context = '' # End the string.
                else:
                    pass # Eat the string character later.
            elif ch == '#':
                # The single-line comment ends the line.
                break 
            elif s[i:i+3] in ('"""', "'''"):
                self.context = s[i:i+3]
            elif ch in ('"', "'"):
                self.context = ch
            elif s[i:] == r'\\\n':
                self.context = 'bs-nl' # The *next* line can't be a def or class.
                break
            elif ch == r'\\':
                i += 1 # Eat the *next* character.
            i += 1
            assert progress < i
        if trace:
            g.trace(
                'indents:', self.base_indent, self.indent,
                'class/def? %5s' % (self.is_class_or_def),
                'continue? %5s' % (self.continues_block()),
                'context: %3s' % repr(self.context),
                s.rstrip())
    #@-others
#@+node:ekr.20161029120457.1: ** class PythonScanner (legacy: to be replaced)
class PythonScanner(basescanner.BaseScanner):
    #@+others
    #@+node:ekr.20161029120457.2: *3*  __init__ (PythonScanner)
    def __init__(self, importCommands, atAuto):
        # Init the base class.
        basescanner.BaseScanner.__init__(self, importCommands, atAuto=atAuto, language='python')
        # Set the parser delims.
        self.lineCommentDelim = '#'
        self.classTags = ['class',]
        self.functionTags = ['def',]
        self.ignoreBlankLines = True
        self.blockDelim1 = self.blockDelim2 = None
            # Suppress the check for the block delim.
            # The check is done in skipSigTail.
        self.strict = True
    #@+node:ekr.20161029120457.3: *3* adjustDefStart (PythonScanner)
    def adjustDefStart(self, s, i):
        '''A hook to allow the Python importer to adjust the
        start of a class or function to include decorators.
        '''
        # Invariant: i does not change.
        # Invariant: start is the present return value.
        try:
            assert s[i] != '\n'
            start = j = g.find_line_start(s, i) if i > 0 else 0
            # g.trace('entry',j,i,repr(s[j:i+10]))
            assert j == 0 or s[j - 1] == '\n'
            while j > 0:
                progress = j
                j1 = j = g.find_line_start(s, j - 2)
                # g.trace('line',repr(s[j:progress]))
                j = g.skip_ws(s, j)
                if not g.match(s, j, '@'):
                    break
                k = g.skip_id(s, j + 1)
                word = s[j: k]
                # Leo directives halt the scan.
                if word and word in g.globalDirectiveList:
                    break
                # A decorator.
                start = j = j1
                assert j < progress
            # g.trace('**returns %s, %s' % (repr(s[start:i]),repr(s[i:i+20])))
            return start
        except AssertionError:
            g.es_exception()
            return i
    #@+node:ekr.20161029120457.4: *3* extendSignature
    def extendSignature(self, s, i):
        '''Extend the text to be added to the class node following the signature.

        The text *must* end with a newline.'''
        # Add a docstring to the class node,
        # And everything on the line following it
        j = g.skip_ws_and_nl(s, i)
        if g.match(s, j, '"""') or g.match(s, j, "'''"):
            j = g.skip_python_string(s, j)
            if j < len(s): # No scanning error.
                # Return the docstring only if nothing but whitespace follows.
                j = g.skip_ws(s, j)
                if g.is_nl(s, j):
                    return j + 1
        return i
    #@+node:ekr.20161029120457.5: *3* findClass (PythonScanner)
    def findClass(self, p):
        '''Return the index end of the class or def in a node, or -1.'''
        s, i = p.b, 0
        while i < len(s):
            progress = i
            if s[i] in (' ', '\t', '\n'):
                i += 1
            elif self.startsComment(s, i):
                i = self.skipComment(s, i)
            elif self.startsString(s, i):
                i = self.skipString(s, i)
            elif self.startsClass(s, i):
                return 'class', self.sigStart, self.codeEnd
            elif self.startsFunction(s, i):
                return 'def', self.sigStart, self.codeEnd
            elif self.startsId(s, i):
                i = self.skipId(s, i)
            else:
                i += 1
            assert progress < i, 'i: %d, ch: %s' % (i, repr(s[i]))
        return None, -1, -1
    #@+node:ekr.20161029120457.6: *3* skipCodeBlock (PythonScanner) & helpers
    def skipCodeBlock(self, s, i, kind):
        trace = False; verbose = True
        # if trace: g.trace('***',g.callers())
        startIndent = self.startSigIndent
        if trace: g.trace('startIndent', startIndent)
        assert startIndent is not None
        i = start = g.skip_ws_and_nl(s, i)
        parenCount = 0
        underIndentedStart = None # The start of trailing underindented blank or comment lines.
        while i < len(s):
            progress = i
            ch = s[i]
            if g.is_nl(s, i):
                if trace and verbose: g.trace(g.get_line(s, i))
                backslashNewline = (i > 0 and g.match(s, i - 1, '\\\n'))
                if backslashNewline:
                    # An underindented line, including docstring,
                    # does not end the code block.
                    i += 1 # 2010/11/01
                else:
                    i = g.skip_nl(s, i)
                    j = g.skip_ws(s, i)
                    if g.is_nl(s, j):
                        pass # We have already made progress.
                    else:
                        i, underIndentedStart, breakFlag = self.pythonNewlineHelper(
                            s, i, parenCount, startIndent, underIndentedStart)
                        if breakFlag: break
            elif ch == '#':
                i = g.skip_to_end_of_line(s, i)
            elif ch == '"' or ch == '\'':
                i = g.skip_python_string(s, i)
            elif ch in '[{(':
                i += 1; parenCount += 1
                # g.trace('ch',ch,parenCount)
            elif ch in ']})':
                i += 1; parenCount -= 1
                # g.trace('ch',ch,parenCount)
            else: i += 1
            assert(progress < i)
        # The actual end of the block.
        if underIndentedStart is not None:
            i = underIndentedStart
            if trace: g.trace('***backtracking to underindent range')
            if trace: g.trace(g.get_line(s, i))
        if 0 < i < len(s) and not g.match(s, i - 1, '\n'):
            g.trace('Can not happen: Python block does not end in a newline.')
            g.trace(g.get_line(s, i))
            return i, False
        # 2010/02/19: Include all following material
        # until the next 'def' or 'class'
        i = self.skipToTheNextClassOrFunction(s, i, startIndent)
        if (trace or self.trace) and s[start: i].strip():
            g.trace('%s returns\n' % (kind) + s[start: i])
        return i, True
    #@+node:ekr.20161029120457.7: *4* pythonNewlineHelper
    def pythonNewlineHelper(self, s, i, parenCount, startIndent, underIndentedStart):
        trace = False
        breakFlag = False
        j, indent = g.skip_leading_ws_with_indent(s, i, self.tab_width)
        if trace: g.trace(
            'startIndent', startIndent, 'indent', indent, 'parenCount', parenCount,
            'line', repr(g.get_line(s, j)))
        if indent <= startIndent and parenCount == 0:
            # An underindented line: it ends the block *unless*
            # it is a blank or comment line or (2008/9/1) the end of a triple-quoted string.
            if g.match(s, j, '#'):
                if trace: g.trace('underindent: comment')
                if underIndentedStart is None: underIndentedStart = i
                i = j
            elif g.match(s, j, '\n'):
                if trace: g.trace('underindent: blank line')
                # Blank lines never start the range of underindented lines.
                i = j
            else:
                if trace: g.trace('underindent: end of block')
                breakFlag = True # The actual end of the block.
        else:
            if underIndentedStart and g.match(s, j, '\n'):
                # Add the blank line to the underindented range.
                if trace: g.trace('properly indented blank line extends underindent range')
            elif underIndentedStart and g.match(s, j, '#'):
                # Add the (properly indented!) comment line to the underindented range.
                if trace: g.trace('properly indented comment line extends underindent range')
            elif underIndentedStart is None:
                pass
            else:
                # A properly indented non-comment line.
                # Give a message for all underindented comments in underindented range.
                if trace: g.trace('properly indented line generates underindent errors')
                s2 = s[underIndentedStart: i]
                lines = g.splitlines(s2)
                for line in lines:
                    if line.strip():
                        junk, indent = g.skip_leading_ws_with_indent(line, 0, self.tab_width)
                        if indent <= startIndent:
                            if j not in self.errorLines: # No error yet given.
                                self.errorLines.append(j)
                                self.underindentedComment(line)
                underIndentedStart = None
        if trace: g.trace('breakFlag', breakFlag, 'returns', i, 'underIndentedStart', underIndentedStart)
        return i, underIndentedStart, breakFlag
    #@+node:ekr.20161029120457.8: *4* skipToTheNextClassOrFunction (New in 4.8)
    def skipToTheNextClassOrFunction(self, s, i, lastIndent):
        '''Skip to the next python def or class.
        Return the original i if nothing more is found.
        This allows the "if __name__ == '__main__' hack
        to appear at the top level.'''
        return i # A rewrite is needed.
    #@+node:ekr.20161029120457.9: *3* skipSigTail
    # This must be overridden in order to handle newlines properly.

    def skipSigTail(self, s, i, kind):
        '''Skip from the end of the arg list to the start of the block.'''
        if 1: # New code
            while i < len(s):
                ch = s[i]
                if ch == ':':
                    return i, True
                elif ch == '\n':
                    return i, False
                elif self.startsComment(s, i):
                    i = self.skipComment(s, i)
                else:
                    i += 1
            return i, False
        else: # old code
            while i < len(s):
                ch = s[i]
                if ch == '\n':
                    break
                elif ch in (' ', '\t',):
                    i += 1
                elif self.startsComment(s, i):
                    i = self.skipComment(s, i)
                else:
                    break
            return i, g.match(s, i, ':')
    #@+node:ekr.20161029120457.10: *3* skipString
    def skipString(self, s, i):
        # Returns len(s) on unterminated string.
        return g.skip_python_string(s, i, verbose=False)
    #@-others
#@-others
importer_dict = {
    'class': PythonLineScanner if new_scanner else PythonScanner,
    'extensions': ['.py', '.pyw', '.pyi'],
        # mypy uses .pyi extension.
}
#@-leo
