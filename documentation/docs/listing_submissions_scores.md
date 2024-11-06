# Listing your submission forecast skill scores

This section provides an example of how to list your submission forecast skill scores using the Predico API.

This flow allows you to access both your submissions forecast skill scores and relative rank to other forecasters.

## Retrieving your historical submissions:

Here's how you can retrieve the list your past submissions.

```python title="download_submissions_scores.py"
--8<-- "docs/examples/download_submissions_scores.py:10:22"
```

## For each submission, you can then retrieve the forecast skill scores:

```python title="download_submissions_scores.py"
--8<-- "docs/examples/download_submissions_scores.py:24:46"
```


<a href="../examples/download_submissions_scores.py" download="download_submissions_scores.py"><b>Download Full Example</b></a>


### JSON Example Response 
??? example "Click to view Example Response"

    ```json
    {
      "code": 200,
      "data": {
        "personal_metrics": [
          {
            "submission": "41ccbb67-1612-4045-8674-671e7631777d",
            "variable": "q50",
            "metric": "mae",
            "value": 44.231,
            "rank": 1,
            "total_participants": 3
          },
          {
            "submission": "41ccbb67-1612-4045-8674-671e7631777d",
            "variable": "q50",
            "metric": "pinball",
            "value": 22.115,
            "rank": 1,
            "total_participants": 3
          },
          {
            "submission": "41ccbb67-1612-4045-8674-671e7631777d",
            "variable": "q50",
            "metric": "rmse",
            "value": 54.162,
            "rank": 1,
            "total_participants": 3
          }
        ],
        "general_metrics": [
          {
            "submission__variable": "q50",
            "metric": "mae",
            "avg_value": 496.221,
            "min_value": 44.231,
            "max_value": 1392.914,
            "std_value": 634.065
          },
          {
            "submission__variable": "q50",
            "metric": "pinball",
            "avg_value": 248.11,
            "min_value": 22.115,
            "max_value": 696.457,
            "std_value": 317.032
          },
          {
            "submission__variable": "q50",
            "metric": "rmse",
            "avg_value": 511.077,
            "min_value": 54.162,
            "max_value": 1416.82,
            "std_value": 640.465
          }
        ]
      }
    }
    ```