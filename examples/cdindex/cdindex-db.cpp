/*
 *  Calculate the CD5 index of Crossref works published 1945-2023
 *  from a previously populated database.
 *  The CD5 values until of works published in the range 2017-2023 must
 *  be discarded as they lack the required citations from five year
 *  subsequent publications.
 *
 */

#include <algorithm>
#include <atomic>
#include <cstdlib>
#include <ctime>
#include <execution>
#include <iostream>
#include <map>
#include <string>
#include <utility>

#include <sqlite_modern_cpp.h>
#include <cdindex.h>

#define END_YEAR 2023
#define RANGE "published_year BETWEEN 1945 and 2023"
// #define RANGE "published_year BETWEEN 1945 and 1946"

using namespace  sqlite;
using namespace std;

const bool use_random_values = false;
const int RANDOM_POPULATION_SIZE = 10000000;

// Last timestamp for which CD index can be calculated
timestamp_t HORIZON;


const int BATCH_SIZE = 10000;

// Five years, for calculating the CD_5 index
const int DELTA_YEAR = 5;
const time_t DELTA = DELTA_YEAR * 365 * 24 * 60 * 60;

// Data associated with vertices
class Vdata {
    public:
	vertex_id_t vi;		// Vertex identifier and pointer
	double cdindex;		// Calculated CD index
	Vdata(vertex_id_t id) : vi(id) {}
};

// A map from DOIs to the their vertex and CD index
typedef unordered_map <string, Vdata> s2v_type;
static s2v_type s2v;

typedef pair<s2v_type::iterator, s2v_type::iterator> work_type;

static atomic<unsigned long long> work_counter = 0;

/*
 * Return true if a valid CD index can be calculated for the specified
 * node, i.e. if the node has references and its publication time
 * allows the establishment of an N-year focal point.
 */
static bool
valid_cd_index(Vertex *v)
{
    return v->get_out_degree() > 0 && v->get_timestamp() <= HORIZON;
}

/*
 * Calculate CD-index along the passed begin/end range and store it in
 * the vertice's data
 */
static void
worker(work_type &be)
{
    for (auto v = be.first; v != be.second; v++)
	if (valid_cd_index(v->second.vi.v))
	    s2v.at(v->first).cdindex = cdindex(v->second.vi, DELTA);
    work_counter += BATCH_SIZE;
    if (work_counter % 1000000 == 0)
	cerr << "C " << work_counter << endl;
}

// Return the timestamp associated with the specified date
static time_t
timestamp_from_datetime(int year, int month, int day)
{
    struct tm timeinfo = {0};
    timeinfo.tm_year = year - 1900;
    timeinfo.tm_mon = month - 1;
    timeinfo.tm_mday = day;
    return mktime(&timeinfo);
}


// Add work vertices to the graph
static void
add_random_vertices(Graph &graph)
{
    for (int i = 0; i < RANDOM_POPULATION_SIZE; i++) {
	time_t timestamp = timestamp_from_datetime(rand() % 76 + 1945, 1, 1);
	vertex_id_t id = graph.add_vertex(timestamp);
	s2v.insert(s2v_type::value_type(to_string(i), Vdata(id)));
    }
}

// Add work vertices to the graph
static void
add_vertices(database &db, Graph &graph)
{
    int counter = 0;
    for (auto && row : db << "SELECT DISTINCT doi, published_year,"
		"  Coalesce(published_month, 1),"
		"  Coalesce(published_day, 1)"
		"FROM works WHERE " RANGE
		) {
	string doi;
	int year, month, day;
	row >> doi >> year >> month >> day;
	time_t timestamp = timestamp_from_datetime(year, month, day);

	vertex_id_t id = graph.add_vertex(timestamp);
	s2v.insert(s2v_type::value_type(doi, Vdata(id)));

	// cout << doi << ' ' << timestamp << endl;
	if (counter++ % 1000000 == 0)
	    cerr << "N " << counter - 1 << endl;
    }
}

// Add reference edges to the graph
static void
add_edges(database &db, Graph &graph)
{
    int counter = 0;
    for (auto && row : db << "SELECT works.doi, work_references.doi "
	  " FROM works INNER JOIN work_references "
	  "   ON works.id = work_references.work_id"
	  " WHERE work_references.doi is not null") {
	string source_doi, target_doi;
	row >> source_doi >> target_doi;

	auto source_doi_id_iter = s2v.find(source_doi);
	if (source_doi_id_iter == s2v.end())
	    continue;

	auto target_doi_id_iter = s2v.find(target_doi);
	if (target_doi_id_iter == s2v.end())
	    continue;

	add_edge(source_doi_id_iter->second.vi, target_doi_id_iter->second.vi);
	if (counter++ % 100000 == 0)
	    cerr << "E " << counter - 1 << endl;
    }
}

// Add random reference edges to the graph
static void
add_random_edges(Graph &graph)
{
    for (int i = 0; i < RANDOM_POPULATION_SIZE * 11; i++) {
	auto source_doi_id_iter = s2v.find(to_string(rand() % RANDOM_POPULATION_SIZE));
	if (source_doi_id_iter == s2v.end())
	    continue;

	auto target_doi_id_iter = s2v.find(to_string(rand() % RANDOM_POPULATION_SIZE));
	if (target_doi_id_iter == s2v.end())
	    continue;

	add_edge(source_doi_id_iter->second.vi, target_doi_id_iter->second.vi);
    }
}

int
main(int argc, char *argv[])
{
    Graph graph;
    HORIZON = timestamp_from_datetime(END_YEAR - DELTA_YEAR, 12, 31);

    try {
        database cdb(argv[1]);

        cdb << "CREATE INDEX IF NOT EXISTS works_id_idx ON works(id)";
        cerr << "Index works_id_idx ready" << endl;

        cdb << "CREATE INDEX IF NOT EXISTS work_references_work_id_idx"
          " ON work_references(work_id)";
        cerr << "Index work_references_work_id_idx ready" << endl;

	if (use_random_values) {
	    add_random_vertices(graph);
	    add_random_edges(graph);
	} else {
	    add_vertices(cdb, graph);
	    add_edges(cdb, graph);
	}

	graph.prepare_for_searching();
	cerr << "Graph ready for searching" << endl;

	// Create large work chunks
	vector <work_type> chunks;
	auto pos = s2v.begin();
	auto begin = pos;
	size_t i;
	for (i = 0; i < s2v.size(); i++, pos++) {
	    if (i > 0 && i % BATCH_SIZE == 0) {
		chunks.push_back(pair{begin, pos});
		begin = pos;
	    }
	}
	if (i > 0 && i % BATCH_SIZE != 0)
	    chunks.push_back(pair{begin, pos});

	// Calculate CD-index
	for_each(execution::par_unseq, chunks.begin(), chunks.end(), worker);
	cerr << "CD index calculated" << endl;

	// Save CD-index
        database rdb(argv[2]);
	rdb << "DROP TABLE IF EXISTS cdindex";
	rdb << "CREATE TABLE cdindex(doi, cdindex)";

	rdb << "BEGIN";
	auto ps = rdb << "INSERT INTO cdindex VALUES(?, ?)";
	int counter = 0;
	for (auto v : s2v) {
	    if (!valid_cd_index(v.second.vi.v))
		continue;
	    ps << v.first << v.second.cdindex;
	    ps++;
	    if (counter++ % 1000000 == 0)
		cerr << "S " << counter - 1 << endl;
	}
	rdb << "COMMIT";
    } catch (exception &e) {
        cout << e.what() << std::endl;
    }
    return 0;
}
