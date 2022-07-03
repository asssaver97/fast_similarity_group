# fast_similarity_group
fast group by Jaccard similarity

How to use
---
python3 main.py parameter1 (parameter2) (parameter3)

Ex.: python3 main.py "./input/test_suites.txt" "b_requests&c_requests|groups" 0.95

parameter1: The file containing the filepath of all cases.

parameter2:(optional) The regular expression for the field to filter. The default is "b_requests&c_requests".

parameter3:(optional) The Jaccard Samilarity as the threshold. The default is 0.95.