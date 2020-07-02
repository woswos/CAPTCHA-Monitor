# Contributing

_First off, thanks for spending your time to contribute!_

This project was born from getting frustrated with CAPTCHAs while using the 
[Tor Browser](https://www.torproject.org/) and the ticket 
[#33010](https://trac.torproject.org/projects/tor/ticket/33010) on Tor's trac 
ticketing system. 

## Ways to contribute
- Reporting bugs
- Pull requests
- Documentation
- Suggesting enhancements
- Developing a new feature

## How does this thing work?
I would suggest taking a look at the 
[wiki page](https://gitlab.torproject.org/woswos/CAPTCHA-Monitor/-/wikis/home).
Please feel free to create an issue or reach me to ask questions.

## Developing new features
You can check the open issues to find suggestions made by others 
(most probably me at the moment) and try implementing those. If you have
a completely new feature to add, I would suggest creating an issue first to get
feedback. Please consider the specifications below while writing any code.

## Specifications
Here I will explain the specifications for different types of code within the
CAPTCHA Monitor, starting from the lowest level code.

### Database utilities
#### [Level 0] Low level utilities that interact with the database
* Low level utilities such as `sqlite.py` should provide abstracted access to 
the underlying database type
* The purpose of these types of utilities is to have a modular design and to
be able to use different database types without changing the higher level code
* These utilities should have small, simple, and generic functions
* They shouldn't have functions that do multiple specialized tasks
* These functions should ask for a database or table name for performing their
operations
* Some of the function examples for this category are `insert_entry_into_table()`,
`get_table_entries()`, `update_table_entry()`, etc.
* These functions should return the data to the caller in to form of valid JSON
lists
* Each database row should be a different annotated JSON value in the list
* Database column names need to correspond to individual JSON keys and row values
need to correspond to JSON values for the keys. For example: 
```Python
[
    {
      "additional_headers": "None",
      "browser_version": "9.5",
      "captcha_sign": "Cloudflare",
      "claimed_by": "0",
      "exit_node": "None",
      "expected_hash": "None",
      "id": 1,
      "method": "tor_browser",
      "tbb_security_level": "low",
      "url": "https://example.com"
    },
    {
      "additional_headers": "None",
      "browser_version": "9.5",
      "captcha_sign": "Cloudflare",
      "claimed_by": "0",
      "exit_node": "None",
      "expected_hash": "None",
      "id": 1,
      "method": "tor_browser",
      "tbb_security_level": "low",
      "url": "https://example.com/complex.html"
    }
]
```
* The functions should return an empty list `[]` if the database query didn't
return any results
* A function should return `True` or `False` if it was designed for updating a
database value. `True` should be returned if the operation was successful and
`False` if the operation wasn't successful.
* This level of functions shouldn't process the data gathered from the database
and should transparently transmit the database result to the caller
* So, this level of functions more like a "formatting" and "unifying" level for
the _Level 1_ code
* No code other than _Level 1_ code may not call _Level 0_ code directly

#### [Level 1] Higher level utilities that interact with low level utilities
* Higher level utilities such as `queue.py`, `relays.py`, `tests.py` are responsible
for providing correct table/database names and parameters to the _Level 0_ 
database utilities
* _Level 1_ code exists so that we can change the low level stuff like the 
database implementation without changing the higher level code
* This level of utilities can use multiple _Level 0_ utilities within a single
_Level 1_ function to perform complex operations
* They don't have to be performing complex operations, but they need to be task-specific
* Some of the function examples for this category are `move_failed_job()`,
`count_remaining_jobs()`, `add_job()`, etc.
* These functions should return the data to the caller in to form of valid JSON
lists
* Each returned value should be a different annotated JSON value in the list
* JSON values might have nested JSON values as long as all of the individual 
JSON values in the list are valid. For example: 
```Python
[
  {
    "firefox": {
      "versions": [
        "68.0"
      ]
    }
  },
  {
    "tor_browser": {
      "versions": [
        "9.5"
      ],
      "option_1": [
        "low",
        "medium",
        "high"
      ]
    }
  }
]
```
* The functions designed for getting data should return `None` if the 
_Level 0_ code executed without errors and returned an empty list `[]`
* The functions should return `True` or `False` if they were designed for updating a
database value. `True` should be returned if the operation was successful and
`False` if the operation wasn't successful.
* The functions may do any kind of data processing before returning the data
gathered from _Level 0_ function to the caller

### Notes for all levels of functions/classes
* Should raise a proper exception in an unexpected event, whenever possible
