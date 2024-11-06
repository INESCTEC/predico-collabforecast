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
