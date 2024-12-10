export type ApplyProcessor = {
	specifications: NetworkXProcessorSpecifications;
};



export type Body_login_login_access_token = {
	grant_type?: string | null;
	username: string;
	password: string;
	scope?: string;
	client_id?: string | null;
	client_secret?: string | null;
};



export type DatasetContent = {
	metadata: DatasetPublic;
	relations: Array<Relation>;
	nodes: Array<Node>;
};



export type DatasetCountSampling = {
	count: number;
};



export type DatasetCreate = {
	name: string;
	specifications: DglkeDatasetSpecifications | StixDatasetSpecifications;
	sampling?: DatasetRatioSampling | DatasetCountSampling | null;
};



export type DatasetPublic = {
	name: string;
	id: number;
	owner_id: number;
	dataset_schema: DatasetSchemaPublic | null;
	statistics: DatasetStatistics | null;
	graph_display_specifications: GraphDisplaySpecifications | null;
	workflows: Array<WorkflowPublic>;
};



export type DatasetRatioSampling = {
	ratio: number;
};



export type DatasetSchemaPublic = {
	created_at?: string | null;
	updated_at?: string | null;
	node_types: Array<NodeType>;
	relation_types: Array<RelationType>;
};



export type DatasetSplit = 'train' | 'validation' | 'test';



export type DatasetStatistics = {
	created_at?: string | null;
	updated_at?: string | null;
	id?: number | null;
	node_type_to_property_to_statistics?: Record<string, Record<string, SymbolicPropertyStatistics | NumericPropertyStatistics | null>>;
	relation_type_to_property_to_statistics?: Record<string, Record<string, SymbolicPropertyStatistics | NumericPropertyStatistics | null>>;
};



export type DatasetsPublic = {
	data: Array<DatasetPublic>;
	count: number;
};



export type DglkeDatasetSpecifications = {
	initial_dataset: DlgkeAvailableDataset;
	splits: Array<DatasetSplit>;
	/**
	 * If set to `True`, only one relation type with name `relation` will be created to fit all relations from the dataset, and a property with name `_relation_type` will be added to each relation to specify the original relation type. This behaviour is usefull because some datasets have thousands of relation types and kuzu does not cope well with it. If set to `False`, each relation type will be created as a separate relation type.
	 */
	one_relation_type?: boolean;
};



export type DlgkeAvailableDataset = 'KGDatasetFB15k' | 'KGDatasetWN18';



export type GraphDisplaySpecifications = {
	id?: number | null;
	node_label_field_name?: string | null;
	node_icons?: Record<string, string> | null;
};



export type HTTPValidationError = {
	detail?: Array<ValidationError>;
};



export type ItemCreate = {
	title: string;
	description?: string | null;
};



export type ItemPublic = {
	title: string;
	description?: string | null;
	id: number;
	owner_id: number;
};



export type ItemUpdate = {
	title?: string | null;
	description?: string | null;
};



export type ItemsPublic = {
	data: Array<ItemPublic>;
	count: number;
};



export type Message = {
	message: string;
};



/**
 * Specifications on how to run NetworkX Hits algorithm on the graph and save result (i.e. authority and hub values)
 */
export type NetworkXHitsSpecifications = {
	/**
	 * The field to save authority in.
	 */
	authority_property_name: string;
	/**
	 * The field to save hub in.
	 */
	hub_property_name: string;
	/**
	 * Maximum number of iterations in power method.
	 */
	max_iter?: number;
	/**
	 * Error tolerance used to check convergence in power method iteration.
	 */
	tol?: number;
	/**
	 * Normalize results by the sum of all of the values.
	 */
	normalized?: boolean;
};



/**
 * Specifications on how to run NetworkX PageRank algorithm on the graph and save result (i.e. pagerank values)
 */
export type NetworkXPagerankSpecifications = {
	/**
	 * The field to save pagerank in.
	 */
	pagerank_property_name: string;
	/**
	 * Whether or not graph should be considered as directed while running the algorithm.
	 */
	directed: boolean;
	/**
	 * Damping parameter for PageRank.
	 */
	alpha?: number;
};



export type NetworkXProcessorSpecifications = {
	algorithm_specifications: NetworkXPagerankSpecifications | NetworkXHitsSpecifications;
};



export type NewPassword = {
	token: string;
	new_password: string;
};



export type Node = {
	id: string;
	type: string;
	data?: Record<string, unknown>;
};



export type NodeProperty = {
	name: string;
	type: string;
	is_primary_key?: boolean;
};



export type NodeType = {
	name: string;
	properties: Array<NodeProperty>;
};



export type NumericPropertyInterval = {
	/**
	 * Number of cuts used to split values span.
	 */
	n: number;
	/**
	 * The list of cuts, whether quantiles or bins, expressed with their min value, max value and number of values they contain.
	 */
	min_max_counts: Array<unknown[]>;
};



export type NumericPropertyStatistics = {
	min: unknown;
	max: unknown;
	mean: unknown;
	median: unknown;
	std: unknown;
	quantiles: Array<NumericPropertyInterval>;
	bins: Array<NumericPropertyInterval>;
};



export type Relation = {
	source: string;
	target: string;
	type: string;
	data?: Record<string, unknown>;
};



export type RelationProperty = {
	name: string;
	type: string;
};



export type RelationType = {
	name: string;
	properties: Array<RelationProperty>;
};



/**
 * Enumeration of state types.
 */
export type StateType = 'SCHEDULED' | 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED' | 'CRASHED' | 'PAUSED' | 'CANCELLING';



export type StixDatasetSpecifications = {
	files_content: Array<string>;
};



export type SymbolicPropertyStatistics = {
	/**
	 * Maximum number of items which have been saved in value_counts; if None, value_counts is untouched.
	 */
	value_counts_max: number | null;
	/**
	 * The list of existing values with their count, sorted in descending order and optinally truncated to `value_counts_max`.
	 */
	value_counts: Array<unknown[]>;
};



export type Token = {
	access_token: string;
	token_type?: string;
};



export type UpdatePassword = {
	current_password: string;
	new_password: string;
};



export type UserCreate = {
	email: string;
	is_active?: boolean;
	is_superuser?: boolean;
	full_name?: string | null;
	password: string;
};



export type UserPublic = {
	email: string;
	is_active?: boolean;
	is_superuser?: boolean;
	full_name?: string | null;
	id: number;
};



export type UserRegister = {
	email: string;
	password: string;
	full_name?: string | null;
};



export type UserUpdate = {
	email?: string | null;
	is_active?: boolean;
	is_superuser?: boolean;
	full_name?: string | null;
	password?: string | null;
};



export type UserUpdateMe = {
	full_name?: string | null;
	email?: string | null;
};



export type UsersPublic = {
	data: Array<UserPublic>;
	count: number;
};



export type ValidationError = {
	loc: Array<string | number>;
	msg: string;
	type: string;
};



export type WorkflowPublic = {
	type: WorkflowType;
	description: string;
	state: StateType;
	id: number;
	owner_id: number;
	related_dataset_id: number | null;
};



export type WorkflowType = 'build_dataset' | 'run_processor';

