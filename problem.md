# The problem (Query)

The problem is given a query in a boolean format, and a 2D environment (with no obstacles) with 2 robots and N locations, create an optimal plan to solve the query. The query can be solved by moving the robots to points in the environment. Each point can contain information in the form of boolean properties. Queries are composed of logical conjunctions (XOR, AND, OR). So solving the queries involve having the robots slowly piece together information regarding the query and finally deducing the answer in the form of truth or falsehood.

Properties also follow constraints of the world, relationships between properties must be true. For example, if property "A" is true and property "B" is true, then it implies that properties "C" and "D" will be false.

# The BDD
The binary decision diagram is the combination of the world boolean formula and the query boolean formula. The world must be true 