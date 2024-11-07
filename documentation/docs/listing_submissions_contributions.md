# Listing your submission forecast skill scores

This section provides an example of how to list your submission forecast skill scores using the Predico API.

This flow allows you to access both your submissions forecast skill scores and relative rank to other forecasters.

## Retrieving your historical submissions:

Here's how you can retrieve the list your past submissions.

```python title="download_submissions_contributions.py"
--8<-- "docs/examples/download_submissions_contributions.py:10:22"
```

## For each submission, you can then retrieve the forecast skill scores:

```python title="download_submissions_contributions.py"
--8<-- "docs/examples/download_submissions_contributions.py:24:46"
```


<a href="../examples/download_submissions_contributions.py" download="download_submissions_contributions.py"><b>Download Full Example</b></a>


### JSON Example Response 
??? example "Click to view Example Response"

    ```json
    {
      "code": 200,
      "data": [
        {
          "ensemble": "ac63fe9a-302c-45a1-bbe6-812b85f48dc2",
          "variable": "q10",
          "rank": 1,
          "total_participants": 3
        },
        {
          "ensemble": "87380061-cefe-4bc4-9aaa-87d9304dd342",
          "variable": "q90",
          "rank": 1,
          "total_participants": 3
        },
        {
          "ensemble": "96afa99b-adbe-41ec-8a6c-16c092367520",
          "variable": "q50",
          "rank": 1,
          "total_participants": 3
        }
      ]
    }
    ```