FAQ: Frequently asked questions
-------------------------------

Is sampling peformed before or after the row selection?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Sampling is a powerful optimization applied before any other operation.
Sampling is exactly the same as running Alexandria3k on a directory
with fewer containers.
With a low enough sample (e.g. `random.random() < 0.0002`),
a Crossref scan will complete in seconds.
This allows you to quickly verify a workflow's steps.

Will sampling consistently populate a work's related tables?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Sampling is performed deterministically over each data source's
records or containers.
For example, in the case of Crossref, each container has data
(e.g. title, authors, subjects, funders, references)
for a few thousand complete publications.
When it is skipped through sampling all related data are skipped,
when it is included all related data can be included.

How does row selection affect dependent data?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
By design the row selection for a table also affects the tables
that depend on it.
If e.g. you select a single work, then that work's references
and only those can be included in the references table.
If you select an author all the author's affiliations can be included.
