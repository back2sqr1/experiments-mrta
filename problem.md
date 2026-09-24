# The problem (Query)

The problem is given a query in a boolean format, and a 2D environment (with no obstacles) with 2 robots and N locations, create an optimal plan to solve the query. The query can be solved by moving the robots to points in the environment. Each point can contain information in the form of boolean properties. Queries are composed of logical conjunctions (XOR, AND, OR). So solving the queries involve having the robots slowly piece together information regarding the query and finally deducing the answer in the form of truth or falsehood.

Properties also follow constraints of the world, relationships between properties must be true. For example, if property "A" is true and property "B" is true, then it implies that properties "C" and "D" will be false.

# The investigation space (not to be confused with the world constraints)

The investigation space is the set of 2d coordinate locations called investigation sites, and each of those sites contain a set of properties that are involved with the query. Robots in this environment will assume tasks that involve going to these locations and gaining properties when reaching these sites. Each site's information is static, so no information is changed during the execution and motion of robots.  

# The BDD
The binary decision diagram is the combination of the world boolean formula and the query boolean formula. The world must be true for the query to be true. The world is another condition. The BDD can be reordered based on the relationship between properties and this is done through swaps between adjacent layers of the BDD

# The Search

The search will be done through an AND/OR Search, where the ANDs are possible robot assignments, and the ORs are world resolutions. Robot assignments are ways to assign robots to tasks. Each task is an atomic goal where a robot goes to a single point in the environment. At any given moment, a robot is either assigned to move to a point on the investigation space or not moving at all (either going to a investigation site or hedging or not moving). We determine where the robot is moving at the AND nodes. At each AND node in the search, the system will look at all the robots and create a mapping of where the robot should go. This also could mean that the robot can change course midway through a search. During assignments, at least one robot should be progressing through the BDD, the others are speculative and anticipating where to go. After assignment, all the robots will move to their respective positions, once one robot in the fleet reaches a point, add that information into what is known amongst the robots, and then ask for another assignment. New information should dictate where the robots should go. At any point, when new information is learned, the OR node should determine the resolutions of how the properties should go. If a property is true, then the next AND node should dictate what happens next. If the property is false, then do the corresponding assignment in the next AND node. 

Progression through the bdd involves tracing through the bdd. Starting at the root node, the robots are asked what property it should investigate first. That should be where the non-speculative robot should go. Then when that property is learned, either the robots investigate the bdd if the property is false or true. That tracing is progression through the bdd. While gathering information, the robots can get information that can be learned opportunistically. So if the current property on that needs to be investigated by the bdd is property a, and a speculative robot goes to property c because it might need it later on, then onces a is figured out, if the bdd asks for property c, we can progress through the bdd no cost. Does that make sense? Otherwise, I'm going to answer the next questions after 
your reply

Assumptions:
  - All robots move at the same speed.
  - What one robot learns, the others know immediately.
  - A course change can only happen at a decision moment, because nothing gets decided between them. A robot still travelling gets its new destination from wherever it is, and the distance it already covered still counts.

1. A plan is better then the distribution of outcomes (these are based on the possible property resolutions) is better. This will be 
measured by average time. 
2. A spare robot can go anywhere, but there are obviously coordinates that are better for robots than others. 
3. sifting should be based on plan cost, and for now, lets do size but consider plan-cost later. If you want to start coding, code bit my
bit, in phases so I can review
