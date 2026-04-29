---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/python-custom.html
fetched_at: 2026-04-29
category: processors
---

# Python function

Execute a custom Python function for each row and easily perform complex computations in a Prepare script.

## Options

**Mode**

Select one of three modes for the Python function to run. Each option creates a block of starter code to edit with custom logic. You can choose between non-vectorized or vectorized processing if you use a real Python process.

- Cell: produce a new cell for each row.
  - Non-vectorized: The function receives the data for a row, and must return a single value for each row which is used as the value of the output column.
  - Vectorized: The function receives the input batch of rows as a pandas Dataframe, and must return a pandas Series of the same number of records, which will be used as the values of the output column.

- Row: return a row for each row.
  - Non-vectorized: The function receives the data for a row as a Python dict, and can modify in place all the values of the row. The function returns a Python dictionary. All columns and values of the input rows are replaced by the keys and values of the dictionary.
  - Vectorized: The function receives the input batch of rows as a pandas Dataframe, and must return a pandas Dataframe of the same number of records, which will be used as the values of the output batch of rows (of the same length).

- Rows: produce a list of rows for each row.
  - Non-vectorized: The function receives the data for a row, and can output an arbitrary number of output rows. The function returns an iterable list of rows. The input row is deleted and replaced by all rows returned by the function (so you can have 1->N processing).
  - Vectorized: The function receives the input batch of rows as a pandas Dataframe, and must return an indexed dictionary of vectors, either built by modifying the 'rows' or by returning a pandas DataFrame.

**Error Column**

Create a new column that will be filled with any error messages raised from the Python code.

**Stop on first error**

Stops the processor execution if an error is raised.

**Pass data as unicode**

Read data as unicode.

**Use a real Python process (instead of Jython)**

Change to Python instead of Jython, a reimplementation of Python in Java, and allow vectorized operation to process rows in batches using the Pandas library.

- Selection behavior: Choose an environment: Use DSS builtin env, Inherit project default or Select an environment.
- Used input columns: Add one or more columns to use as input for faster processing.
- Vectorized processing: When selected the input will change from a python dict to a Pandas Dataframe. This provides much improved performance and is strongly recommended when using a real Python process. Operates based on the Cell, Row and Rows options above using Pandas dataframes.

> Note: "The Python function is executed by Jython, which supports only Python 2 and for which only the standard Python library is available." To leverage external libraries, consider using a real Python process or separate Python recipe. The real Python process option enables all standard packages and code libraries.
