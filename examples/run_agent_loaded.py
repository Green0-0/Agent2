import os
import time
from typing import List
from agent2.agent.agent import Agent
from agent2.agent.tool import Tool
from agent2.file import File
from agent2.tools_common.basic_tools.basic_viewing import search_files, view_lines, view_file_raw
from agent2.tools_common.basic_tools.basic_editing import replace_lines_with, replace_block_with, replace_block, replace_lines
from agent2.tools_common.element_tools.element_viewing import view_element, search_elements, view_file, semantic_search_elements
from agent2.tools_common.element_tools.element_editing import replace_element, replace_element_with, open_element
from agent2.utils.utils import load_project_files, get_completion, get_rating_keys
from agent2.utils.agent_utils import load_agent_from_json

def test_github_issue_solver():
    # Initialize tools
    tools = [
        Tool(view_element),
        Tool(replace_element),
        Tool(replace_element_with),
        Tool(search_elements),
        Tool(view_file),
        Tool(open_element)
    ]

    # Test cases
    test_cases = [   
        """QTable cannot take `dimensionless_unscaled` when creating table from `data`
### Description

Attempting to create an table with a column in units `dimensionless_unscaled` leads to a crash, because a guard against setting a column attribute to `np.ma.masked` or `None` triggers a comparison between `np.ma.masked` and Unit which eventually resolves to a `ZeroDivisionError`.

### Expected behavior

A `QTable` is created. 

### How to Reproduce

```python
from astropy.table import QTable, Column
import numpy as np
data = np.ones((5,2))
tt = QTable(data=data, names=["a","weight"],units={"weight":u.dimensionless_unscaled})
```
Results in 
```
---------------------------------------------------------------------------
ZeroDivisionError                         Traceback (most recent call last)
Cell In[15], line 2
      1 data = np.ones((5,2))
----> 2 tt = QTable(data=data, names=["a","weight"],units={"weight":u.dimensionless_unscaled})
      3 tt

File ~/miniconda3/envs/datapipe-testbench/lib/python3.11/site-packages/astropy/table/table.py:887, in Table.__init__(self, data, masked, names, dtype, meta, copy, rows, copy_indices, units, descriptions, **kwargs)
    884 if self.masked not in (None, True, False):
    885     raise TypeError("masked property must be None, True or False")
--> 887 self._set_column_attribute("unit", units)
    888 self._set_column_attribute("description", descriptions)

File ~/miniconda3/envs/datapipe-testbench/lib/python3.11/site-packages/astropy/table/table.py:921, in Table._set_column_attribute(self, attr, values)
    918     if value.strip() == "":
    919         value = None
--> 921 if value not in (np.ma.masked, None):
    922     col = self[name]
    923     if attr == "unit" and isinstance(col, Quantity):
    924         # Update the Quantity unit in-place

File ~/miniconda3/envs/datapipe-testbench/lib/python3.11/site-packages/numpy/ma/core.py:4182, in MaskedArray.__eq__(self, other)
   4171 def __eq__(self, other):
   4172     \"\"\"Check whether other equals self elementwise.
   4173 
   4174     When either of the elements is masked, the result is masked as well,
   (...)
   4180     and other considered equal only if both were fully masked.
   4181     \"\"\"
-> 4182     return self._comparison(other, operator.eq)

File ~/miniconda3/envs/datapipe-testbench/lib/python3.11/site-packages/numpy/ma/core.py:4138, in MaskedArray._comparison(self, other, compare)
   4134 else:
   4135     # For regular arrays, just use the data as they come.
   4136     sdata = self.data
-> 4138 check = compare(sdata, odata)
   4140 if isinstance(check, (np.bool_, bool)):
   4141     return masked if mask else check

File ~/miniconda3/envs/datapipe-testbench/lib/python3.11/site-packages/astropy/units/core.py:955, in UnitBase.__eq__(self, other)
    952     return NotImplemented
    954 try:
--> 955     return is_effectively_unity(self._to(other))
    956 except UnitsError:
    957     return False

File ~/miniconda3/envs/datapipe-testbench/lib/python3.11/site-packages/astropy/units/core.py:1157, in UnitBase._to(self, other)
   1147     # Check quickly whether equivalent.  This is faster than
   1148     # `is_equivalent`, because it doesn't generate the entire
   1149     # physical type list of both units.  In other words it "fails
   1150     # fast".
   1151     if self_decomposed.powers == other_decomposed.powers and all(
   1152         self_base is other_base
   1153         for (self_base, other_base) in zip(
   1154             self_decomposed.bases, other_decomposed.bases
   1155         )
   1156     ):
-> 1157         return self_decomposed.scale / other_decomposed.scale
   1159 raise UnitConversionError(f"'{self!r}' is not a scaled version of '{other!r}'")

ZeroDivisionError: float division by zero
```



### Versions

```python
import astropy
try:
    astropy.system_info()
except AttributeError:
    import platform; print(platform.platform())
    import sys; print("Python", sys.version)
    import astropy; print("astropy", astropy.__version__)
    import numpy; print("Numpy", numpy.__version__)
    import erfa; print("pyerfa", erfa.__version__)
    try:
        import scipy
        print("Scipy", scipy.__version__)
    except ImportError:
        print("Scipy not installed")
    try:
        import matplotlib
        print("Matplotlib", matplotlib.__version__)
    except ImportError:
        print("Matplotlib not installed")
```
```
Linux-5.15.0-119-generic-x86_64-with-glibc2.35
Python 3.11.8 | packaged by conda-forge | (main, Feb 16 2024, 20:53:32) [GCC 12.3.0]
astropy 5.3.4
Numpy 1.26.4
pyerfa 2.0.0
Scipy 1.11.4
Matplotlib 3.8.3
```""",
                        
        """BUG: tables do not deal well with zero-sized string columns
### Description

@saimn [noted](https://github.com/astropy/astropy/pull/16894#issuecomment-2314640002) in #16894 that zero sized data are a problem:
```
import numpy as np
from astropy.io import fits
from astropy.table import QTable, Table
data = np.array([("", 12)], dtype=[("a", "S"), ("b", "i4")])
fits.BinTableHDU(data).writeto("zerodtable.fits", overwrite=True)
t = Table.read("zerodtable.fits")
t

File ~/dev/astropy/astropy/astropy/table/pprint.py:295, in TableFormatter._pformat_col(self, col, max_lines, show_name, show_unit, show_dtype, show_length, html, align)
    283 col_strs_iter = self._pformat_col_iter(
    284     col,
    285     max_lines,
   (...)
    290     outs=outs,
    291 )
    293 # Replace tab and newline with text representations so they display nicely.
    294 # Newline in particular is a problem in a multicolumn table.
--> 295 col_strs = [
    296     val.replace("\t", "\\t").replace("\n", "\\n") for val in col_strs_iter
    297 ]
    298 if len(col_strs) > 0:
    299     col_width = max(len(x) for x in col_strs)

File ~/dev/astropy/astropy/astropy/table/pprint.py:452, in TableFormatter._pformat_col_iter(self, col, max_lines, show_name, show_unit, outs, show_dtype, show_length)
    450 n_header += 1
    451 if dtype is not None:
--> 452     col_dtype = dtype_info_name((dtype, multidims))
    453 else:
    454     col_dtype = col.__class__.__qualname__ or "object"

File ~/dev/astropy/astropy/astropy/utils/data_info.py:100, in dtype_info_name(dtype)
     74 def dtype_info_name(dtype):
     75     \"\"\"Return a human-oriented string name of the ``dtype`` arg.
     76     This can be use by astropy methods that present type information about
     77     a data object.
   (...)
     98         String name of ``dtype``
     99     \"\"\"
--> 100     dtype = np.dtype(dtype)
    101     if dtype.names is not None:
    102         info_names = ", ".join(dtype_info_name(dt[0]) for dt in dtype.fields.values())

ValueError: invalid itemsize in generic type tuple
```
This problem is in displaying, not creating the table:
```
t["a"]
<MaskedColumn name='a' dtype='bytes0' length=1>
--
```
The display problem seems a bug in numpy - https://github.com/numpy/numpy/issues/27301 - but one we should work around for now.

Furthermore, `QTable` can read it, but changes the size
```
QTable.read("zerodtable.fits")
<QTable length=1>
  a      b  
bytes1 int32
------ -----
    --    12
```

This turns out to be because in `io`, for table subclasses, one does `QTable(table)` - and with a copy this changes the dtype."""
    ]

    # Process each test case
    for issue_num, issue in enumerate(test_cases, start=1):
        print(f"**** Processing Issue #{issue_num} ****")
        
        print("Loading files...")
        project_files = load_project_files()
        
        print("Loaded files...")
        
        # Load solver agent
        agent = load_agent_from_json("saved_agents/codeact_agent.json", tools)
        
        # Start agent with current task
        agent.start(task=issue, files=project_files)
        
        # Agent interaction loop
        while True:
            oai_messages = agent.cached_state.chat.toOAI()
            llm_response = get_completion(oai_messages, model="Qwen2.5-Coder-32B-Instruct", api_url="https://api.sambanova.ai/v1")
            if not llm_response:
                break
            response = agent.step(llm_response)
            if response.done:
                break

        # Save modified files
        edit_count = 0
        for file in agent.cached_state.workspace:
            if file.original_content != file.updated_content:
                edit_count += 1
                edit_dir = f"examples/edits/issue_{issue_num}/edit_{edit_count}"
                os.makedirs(edit_dir, exist_ok=True)
                
                # Write modified file
                output_path = os.path.join(edit_dir, os.path.basename(file.path))
                with open(output_path, "w") as f:
                    f.write(file.updated_content)
                
                # Print diff
                print(f"\nEdit #{edit_count} in {file.path}:")
                print(file.diff("astropy"))

        print(f"Completed Issue #{issue_num}")
        print("Accessed elements:")
        for file, element in agent.cached_state.saved_elements:
            print(file + ":" + element)
        print("Testing rating...")
        diffs = []
        for f in agent.cached_state.workspace:
            if f.original_content != f.updated_content:
                diffs += [f.diff(None)]
        diffs = "\n".join(diffs)
        print(diffs)                
        
        # Load rating agent
        rating_agent = load_agent_from_json("saved_agents/rater_agent.json", tools)
        
        # Replace placeholders in the rating agent's init message
        rating_agent.init_message = (
            rating_agent.init_message
            .replace("{{diffs}}", diffs)
        )
        
        # Start agent with current task
        rating_agent.start(task=issue, files=project_files, copy_saved_elements=agent.cached_state.saved_elements)
        # Get response, parse response
        rating_llm_response = get_completion((rating_agent.cached_state.chat.toOAI()), model="Qwen2.5-Coder-32B-Instruct", api_url="https://api.sambanova.ai/v1")
        print(rating_llm_response)
        rating_llm_score = get_rating_keys(rating_llm_response)
        print(rating_llm_score)
        time.sleep(30)  # Rate limit protection

if __name__ == "__main__":
    test_github_issue_solver()