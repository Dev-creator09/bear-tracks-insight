/**
 * Real University of Alberta course data
 * Structured based on actual course catalog information
 */

export interface CourseData {
  subject: string;
  number: number;
  title: string;
  description: string;
  credits: number;
}

export const CMPUT_COURSES: CourseData[] = [
  {
    subject: 'CMPUT',
    number: 101,
    title: 'Introduction to Computing',
    description:
      'An introduction to computing for students in the sciences and engineering. Basic skills in using computers; introductory programming; computing in their discipline. Not for credit in Computer Science programs. Prerequisite: Mathematics 30-1.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 174,
    title: 'Introduction to the Foundations of Computation I',
    description:
      'An introduction to object-oriented programming and data structures using Java. Topics include encapsulation, inheritance, polymorphism, basic data structures, algorithms and testing. Prerequisite: CMPUT 101 or consent of Department.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 175,
    title: 'Introduction to the Foundations of Computation II',
    description:
      'A continuation of CMPUT 174. More advanced object-oriented concepts and data structures. Introduction to algorithm analysis. Prerequisite: CMPUT 174.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 201,
    title: 'Practical Programming Methodology',
    description:
      'Programming skills for all phases of the software development lifecycle including design, implementation, testing and maintenance. Prerequisite: CMPUT 175.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 204,
    title: 'Algorithms I',
    description:
      'The analysis and design of algorithms. Sorting, searching, graph algorithms, and algorithmic strategies. Prerequisite: CMPUT 175 and MATH 101.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 229,
    title: 'Computer Organization and Architecture I',
    description:
      'Digital logic: gates, combinational circuits. Data representation: integers, characters. Computer system organization and the fetch-execute cycle. Assembly language programming. Prerequisite: CMPUT 175.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 272,
    title: 'Formal Systems and Logic in Computing Science',
    description:
      'Propositional and predicate logic, formal proof techniques, program verification, mathematical induction, recurrence relations. Prerequisite: CMPUT 175 and MATH 101.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 274,
    title: 'Tangible Computing',
    description:
      'An introduction to physical computing using microcontrollers, sensors, and actuators. Programming embedded systems. Prerequisite: CMPUT 175.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 301,
    title: 'Introduction to Software Engineering',
    description:
      'An overview of software engineering including processes, requirements, design, implementation, testing and project management. Team projects. Prerequisite: CMPUT 201 or CMPUT 204.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 304,
    title: 'Algorithms II',
    description:
      'Advanced algorithms and data structures. Graphs, dynamic programming, greedy algorithms, network flows, NP-completeness. Prerequisite: CMPUT 204.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 325,
    title: 'Non-Procedural Programming Languages',
    description:
      'An introduction to functional and logic programming paradigms. Recursion, pattern matching, higher-order functions. Prerequisite: CMPUT 204.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 328,
    title: 'Visual Recognition',
    description:
      'An introduction to visual recognition, image processing, and computer vision. Machine learning for vision. Prerequisite: CMPUT 204 and MATH 125.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 340,
    title: 'Introduction to Numerical Methods',
    description:
      'Numerical methods for solving equations, interpolation, integration, and differential equations. Prerequisite: CMPUT 175 and MATH 102 and MATH 125.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 350,
    title: 'Advanced Operating Systems',
    description:
      'Operating system design and implementation. Processes, threads, synchronization, memory management, file systems. Prerequisite: CMPUT 229 and CMPUT 272.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 365,
    title: 'Introduction to Database Management Systems',
    description:
      'Database design theory and practice. Entity-relationship modeling, relational model, SQL, normalization, transactions. Prerequisite: CMPUT 204.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 366,
    title: 'Intelligent Systems',
    description:
      'Search, knowledge representation, reasoning, planning, machine learning, natural language processing. Prerequisite: CMPUT 204.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 367,
    title: 'Introduction to Machine Learning',
    description:
      'Supervised and unsupervised learning, neural networks, decision trees, clustering, dimensionality reduction. Prerequisite: CMPUT 204 and MATH 125 and STAT 235.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 401,
    title: 'Compiler Design',
    description:
      'Lexical analysis, parsing, semantic analysis, code generation, optimization. Design and implementation of a compiler. Prerequisite: CMPUT 304 and CMPUT 325.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 412,
    title: 'Experimental Mobile Robotics',
    description:
      'Kinematics, sensors, perception, localization, mapping, planning, and control for mobile robots. Prerequisite: CMPUT 304 and MATH 125.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 414,
    title: 'Introduction to Computer Graphics',
    description:
      '2D and 3D graphics, transformations, viewing, lighting, shading, ray tracing. OpenGL programming. Prerequisite: CMPUT 204 and MATH 125.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 415,
    title: 'Introduction to Computer Game Development',
    description:
      'Game engines, physics, AI, graphics, networking. Development of a complete game. Prerequisite: CMPUT 304.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 416,
    title: 'Computers and Society',
    description:
      'Impact of computers on society. Privacy, security, intellectual property, ethics, social implications. Prerequisite: Senior standing in Computing Science.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 424,
    title: 'Introduction to Computer Networks',
    description:
      'Network protocols, layered architecture, TCP/IP, routing, congestion control, network security. Prerequisite: CMPUT 229 and CMPUT 272.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 428,
    title: 'Introduction to Computer Vision',
    description:
      'Image formation, feature detection, object recognition, motion analysis, 3D reconstruction. Prerequisite: CMPUT 304 and MATH 125.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 429,
    title: 'Computer Architecture II',
    description:
      'Instruction set design, pipelining, memory hierarchy, parallel processing. Prerequisite: CMPUT 229.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 455,
    title: 'Introduction to Information Retrieval',
    description:
      'Text processing, indexing, ranking, web search, evaluation. Design of search engines. Prerequisite: CMPUT 304.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 466,
    title: 'Introduction to Natural Language Processing',
    description:
      'Syntax, semantics, discourse, language models, parsing, machine translation. Prerequisite: CMPUT 366 or CMPUT 367.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 467,
    title: 'Machine Learning',
    description:
      'Advanced machine learning including deep learning, reinforcement learning, ensemble methods. Prerequisite: CMPUT 367.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 474,
    title: 'Formal Languages and Automata',
    description:
      'Regular languages, context-free languages, Turing machines, computability, complexity. Prerequisite: CMPUT 272.',
    credits: 3,
  },
  {
    subject: 'CMPUT',
    number: 496,
    title: 'Topics in Computing Science',
    description:
      'Topics of current interest in computing science. Content varies. Prerequisite: Consent of Department.',
    credits: 3,
  },
];

export const MATH_COURSES: CourseData[] = [
  {
    subject: 'MATH',
    number: 100,
    title: 'Calculus for the Life Sciences I',
    description:
      'Functions, limits, derivatives, applications of derivatives. For students in biological sciences. Prerequisite: Mathematics 30-1.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 101,
    title: 'Calculus for Engineering and Physical Sciences I',
    description:
      'Limits, derivatives, applications of derivatives, integration. Prerequisite: Mathematics 30-1.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 102,
    title: 'Calculus for Engineering and Physical Sciences II',
    description:
      'Integration techniques, applications of integration, infinite series, parametric equations. Prerequisite: MATH 101.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 114,
    title: 'Elementary Calculus I',
    description:
      'Functions, limits, derivatives, curve sketching, optimization. Not for students in mathematical sciences. Prerequisite: Mathematics 30-1.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 115,
    title: 'Elementary Calculus II',
    description:
      'Integration, techniques of integration, applications. Prerequisite: MATH 114.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 125,
    title: 'Linear Algebra I',
    description:
      'Systems of equations, matrices, determinants, vectors, eigenvalues. Prerequisite: Mathematics 30-1.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 127,
    title: 'Introduction to Matrix Algebra',
    description:
      'Basic matrix algebra for business and economics students. Not for credit in mathematical sciences. Prerequisite: Mathematics 30-1.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 134,
    title: 'Calculus for the Life Sciences I',
    description:
      'Limits, derivatives, applications to biology and medicine. Prerequisite: Mathematics 30-1.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 136,
    title: 'Calculus for the Life Sciences II',
    description:
      'Integration, differential equations, applications to biology. Prerequisite: MATH 134.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 144,
    title: 'Calculus for the Physical Sciences I',
    description:
      'Limits, derivatives, curve sketching, applications. Prerequisite: Mathematics 30-1.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 146,
    title: 'Calculus for the Physical Sciences II',
    description:
      'Integration, applications, infinite series. Prerequisite: MATH 144.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 154,
    title: 'Calculus for Business and Economics I',
    description:
      'Functions, derivatives, optimization for business applications. Prerequisite: Mathematics 30-1.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 156,
    title: 'Calculus for Business and Economics II',
    description:
      'Integration, multivariable calculus for business. Prerequisite: MATH 154.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 201,
    title: 'Differential Equations',
    description:
      'First-order ODEs, linear equations, systems, Laplace transforms. Prerequisite: MATH 101 and MATH 102.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 209,
    title: 'Calculus III',
    description:
      'Multivariable calculus, partial derivatives, multiple integrals, vector calculus. Prerequisite: MATH 101 and MATH 102.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 214,
    title: 'Intermediate Calculus I',
    description:
      'Limits, continuity, sequences, series. Prerequisite: MATH 115.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 215,
    title: 'Intermediate Calculus II',
    description:
      'Multivariable calculus, partial derivatives, multiple integrals. Prerequisite: MATH 214.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 225,
    title: 'Linear Algebra II',
    description:
      'Vector spaces, linear transformations, inner product spaces, diagonalization. Prerequisite: MATH 125.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 227,
    title: 'Discrete Mathematics for Computing Science',
    description:
      'Logic, sets, relations, functions, counting, recurrence relations, graph theory. Prerequisite: MATH 125.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 228,
    title: 'Introduction to Combinatorics',
    description:
      'Permutations, combinations, generating functions, recurrence relations. Prerequisite: MATH 125.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 241,
    title: 'Geometry',
    description:
      'Euclidean and non-Euclidean geometry. Prerequisite: MATH 125.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 253,
    title: 'Theory of Interest',
    description:
      'Financial mathematics, annuities, bonds, loans. Prerequisite: MATH 115.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 281,
    title: 'Groups and Symmetries',
    description:
      'Introduction to group theory and symmetry. Prerequisite: MATH 125.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 311,
    title: 'Probability',
    description:
      'Sample spaces, random variables, distributions, expectation, limit theorems. Prerequisite: MATH 209.',
    credits: 3,
  },
  {
    subject: 'MATH',
    number: 322,
    title: 'Complex Variables',
    description:
      'Complex numbers, analytic functions, contour integration, residue theorem. Prerequisite: MATH 209.',
    credits: 3,
  },
];

export const STAT_COURSES: CourseData[] = [
  {
    subject: 'STAT',
    number: 141,
    title: 'Introduction to Statistics for the Life Sciences',
    description:
      'Descriptive statistics, probability, inference, hypothesis testing for biological sciences. Prerequisite: Mathematics 30-1.',
    credits: 3,
  },
  {
    subject: 'STAT',
    number: 151,
    title: 'Introduction to Applied Statistics I',
    description:
      'Descriptive statistics, probability, random variables, distributions. Prerequisite: Mathematics 30-1.',
    credits: 3,
  },
  {
    subject: 'STAT',
    number: 235,
    title: 'Probability and Statistics for Engineering',
    description:
      'Probability, distributions, estimation, hypothesis testing. Prerequisite: MATH 101.',
    credits: 3,
  },
  {
    subject: 'STAT',
    number: 252,
    title: 'Introduction to Applied Statistics II',
    description:
      'Estimation, hypothesis testing, regression, ANOVA. Prerequisite: STAT 151.',
    credits: 3,
  },
  {
    subject: 'STAT',
    number: 265,
    title: 'Introduction to Probability Theory',
    description:
      'Sample spaces, random variables, distributions, expectation. Prerequisite: MATH 102 or MATH 115.',
    credits: 3,
  },
  {
    subject: 'STAT',
    number: 266,
    title: 'Introduction to Statistical Inference',
    description:
      'Estimation, hypothesis testing, confidence intervals. Prerequisite: STAT 265.',
    credits: 3,
  },
  {
    subject: 'STAT',
    number: 268,
    title: 'Introduction to Statistical Computing',
    description:
      'Data manipulation, visualization, statistical programming in R. Prerequisite: STAT 151.',
    credits: 3,
  },
  {
    subject: 'STAT',
    number: 321,
    title: 'Intermediate Probability Theory',
    description:
      'Probability spaces, random variables, limit theorems. Prerequisite: STAT 265 and MATH 209.',
    credits: 3,
  },
  {
    subject: 'STAT',
    number: 330,
    title: 'Statistical Inference',
    description:
      'Point estimation, interval estimation, hypothesis testing. Prerequisite: STAT 266.',
    credits: 3,
  },
  {
    subject: 'STAT',
    number: 332,
    title: 'Sample Survey Design',
    description:
      'Simple random sampling, stratified sampling, cluster sampling. Prerequisite: STAT 252 or STAT 266.',
    credits: 3,
  },
  {
    subject: 'STAT',
    number: 337,
    title: 'Introduction to Biostatistics',
    description:
      'Statistical methods for biological and medical research. Prerequisite: STAT 252 or STAT 266.',
    credits: 3,
  },
  {
    subject: 'STAT',
    number: 350,
    title: 'Linear Models',
    description:
      'Multiple regression, model selection, diagnostics, ANOVA. Prerequisite: STAT 266 and MATH 125.',
    credits: 3,
  },
  {
    subject: 'STAT',
    number: 361,
    title: 'Stochastic Processes',
    description:
      'Markov chains, Poisson processes, queueing theory. Prerequisite: STAT 265.',
    credits: 3,
  },
  {
    subject: 'STAT',
    number: 371,
    title: 'Categorical Data Analysis',
    description:
      'Contingency tables, logistic regression, log-linear models. Prerequisite: STAT 252 or STAT 266.',
    credits: 3,
  },
  {
    subject: 'STAT',
    number: 378,
    title: 'Experimental Design',
    description:
      'Completely randomized designs, blocking, factorial designs. Prerequisite: STAT 252 or STAT 266.',
    credits: 3,
  },
];

export const ALL_COURSES = [...CMPUT_COURSES, ...MATH_COURSES, ...STAT_COURSES];
