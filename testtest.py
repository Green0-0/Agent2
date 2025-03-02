from agent2.formatting.autoformatter import unenumerate_lines, remove_codeblock

text = """
0 ```python
1  import numpy as np
2 def f(x):
3     return np.sin(x)
4 print f(1)```

"""
print(text)
print(unenumerate_lines(text)[0] )
print(unenumerate_lines(text)[1] )
print(unenumerate_lines(text)[2] )
print(remove_codeblock(text))