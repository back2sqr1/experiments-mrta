# The problem (Query)

The problem is given a query in a boolean format, and a 2D environment (with no obstacles) with 2 robots and N locations, create an optimal plan to solve the query. The query can be solved by moving the robots to points in the environment. Each point can contain information in the form of boolean properties. Queries are composed of logical conjunctions (XOR, AND, OR). So solving the queries involve having the robots slowly piece together information regarding the query and finally deducing the answer in the form of truth or falsehood.

Properties also follow constraints of the world, relationships between properties must be true. For example, if property "A" is true and property "B" is true, then it implies that properties "C" and "D" will be false.

# The investigation space (not to be confused with the world constraints)

The investigation space is the set of 2d coordinate locations called investigation sites, and each of those sites contain a set of properties that are involved with the query. Robots in this environment will assume tasks that involve going to these locations and gaining properties when reaching these sites. Each site's information is static, so no information is changed during the execution and motion of robots.  

# The BDD
The binary decision diagram is the combination of the world boolean formula and the query boolean formula. The world must be true for the query to be true. The world is another condition. The BDD can be reordered based on the relationship between properties and this is done through swaps between adjacent layers of the BDD

# The Search

The search will be done through an AND/OR Search, where the ANDs are possible robot assignments, and the ORs are world resolutions. Robot assignments are ways to assign robots to tasks. Each task is an atomic goal where a robot goes to a single point in the environment 