-- Number of works containing "hello" or "world" in their title or abstract

SELECT Count(*) FROM works
WHERE title LIKE '%hello%' OR abstract LIKE  '%hello%';
