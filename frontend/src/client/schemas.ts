export const $ApplyProcessor = {
	properties: {
		dataset_id: {
	type: 'number',
	isRequired: true,
},
		specifications: {
	type: 'NetworkXProcessorSpecifications',
	isRequired: true,
},
	},
} as const;

export const $Body_login_login_access_token = {
	properties: {
		grant_type: {
	type: 'any-of',
	contains: [{
	type: 'string',
	pattern: 'password',
}, {
	type: 'null',
}],
},
		username: {
	type: 'string',
	isRequired: true,
},
		password: {
	type: 'string',
	isRequired: true,
},
		scope: {
	type: 'string',
	default: '',
},
		client_id: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		client_secret: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
	},
} as const;

export const $DatasetContent = {
	properties: {
		metadata: {
	type: 'DatasetPublic',
	isRequired: true,
},
		relations: {
	type: 'array',
	contains: {
		type: 'Relation',
	},
	isRequired: true,
},
		nodes: {
	type: 'array',
	contains: {
		type: 'Node',
	},
	isRequired: true,
},
	},
} as const;

export const $DatasetCountSampling = {
	properties: {
		count: {
	type: 'number',
	isRequired: true,
	exclusiveMinimum: 0,
},
	},
} as const;

export const $DatasetCreate = {
	properties: {
		name: {
	type: 'string',
	isRequired: true,
},
		specifications: {
	type: 'any-of',
	contains: [{
	type: 'DglkeDatasetSpecifications',
}, {
	type: 'StixDatasetSpecifications',
}],
	isRequired: true,
},
		sampling: {
	type: 'any-of',
	contains: [{
	type: 'DatasetRatioSampling',
}, {
	type: 'DatasetCountSampling',
}, {
	type: 'null',
}],
},
	},
} as const;

export const $DatasetFilters = {
	properties: {
		node_filters: {
	type: 'array',
	contains: {
		type: 'GraphElementFilter',
	},
	isRequired: true,
},
	},
} as const;

export const $DatasetPublic = {
	properties: {
		name: {
	type: 'string',
	isRequired: true,
},
		id: {
	type: 'number',
	isRequired: true,
},
		owner_id: {
	type: 'number',
	isRequired: true,
},
		dataset_schema: {
	type: 'any-of',
	contains: [{
	type: 'DatasetSchemaPublic',
}, {
	type: 'null',
}],
	isRequired: true,
},
		statistics: {
	type: 'any-of',
	contains: [{
	type: 'DatasetStatistics',
}, {
	type: 'null',
}],
	isRequired: true,
},
		graph_display_specifications: {
	type: 'any-of',
	contains: [{
	type: 'GraphDisplaySpecifications',
}, {
	type: 'null',
}],
	isRequired: true,
},
		workflows: {
	type: 'array',
	contains: {
		type: 'WorkflowPublic',
	},
	isRequired: true,
},
	},
} as const;

export const $DatasetRatioSampling = {
	properties: {
		ratio: {
	type: 'number',
	isRequired: true,
	maximum: 1,
	exclusiveMinimum: 0,
},
	},
} as const;

export const $DatasetSchemaPublic = {
	properties: {
		created_at: {
	type: 'any-of',
	contains: [{
	type: 'string',
	format: 'date-time',
}, {
	type: 'null',
}],
},
		updated_at: {
	type: 'any-of',
	contains: [{
	type: 'string',
	format: 'date-time',
}, {
	type: 'null',
}],
},
		node_types: {
	type: 'array',
	contains: {
		type: 'NodeType',
	},
	isRequired: true,
},
		relation_types: {
	type: 'array',
	contains: {
		type: 'RelationType',
	},
	isRequired: true,
},
	},
} as const;

export const $DatasetSplit = {
	type: 'Enum',
	enum: ['train','validation','test',],
} as const;

export const $DatasetStatistics = {
	properties: {
		created_at: {
	type: 'any-of',
	contains: [{
	type: 'string',
	format: 'date-time',
}, {
	type: 'null',
}],
},
		updated_at: {
	type: 'any-of',
	contains: [{
	type: 'string',
	format: 'date-time',
}, {
	type: 'null',
}],
},
		id: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		node_type_to_property_to_statistics: {
	type: 'dictionary',
	contains: {
	type: 'dictionary',
	contains: {
	type: 'any-of',
	contains: [{
	type: 'SymbolicPropertyStatistics',
}, {
	type: 'NumericPropertyStatistics',
}, {
	type: 'null',
}],
},
},
},
		relation_type_to_property_to_statistics: {
	type: 'dictionary',
	contains: {
	type: 'dictionary',
	contains: {
	type: 'any-of',
	contains: [{
	type: 'SymbolicPropertyStatistics',
}, {
	type: 'NumericPropertyStatistics',
}, {
	type: 'null',
}],
},
},
},
	},
} as const;

export const $DatasetsPublic = {
	properties: {
		data: {
	type: 'array',
	contains: {
		type: 'DatasetPublic',
	},
	isRequired: true,
},
		count: {
	type: 'number',
	isRequired: true,
},
	},
} as const;

export const $DglkeDatasetSpecifications = {
	properties: {
		initial_dataset: {
	type: 'DlgkeAvailableDataset',
	isRequired: true,
},
		splits: {
	type: 'array',
	contains: {
		type: 'DatasetSplit',
	},
	isRequired: true,
},
		one_relation_type: {
	type: 'boolean',
	description: `If set to \`True\`, only one relation type with name \`relation\` will be created to fit all relations from the dataset, and a property with name \`_relation_type\` will be added to each relation to specify the original relation type. This behaviour is usefull because some datasets have thousands of relation types and kuzu does not cope well with it. If set to \`False\`, each relation type will be created as a separate relation type.`,
	default: true,
},
	},
} as const;

export const $DlgkeAvailableDataset = {
	type: 'Enum',
	enum: ['KGDatasetFB15k','KGDatasetWN18',],
} as const;

export const $FilterSelect = {
	type: 'Enum',
	enum: ['everything','nothing','custom',],
} as const;

export const $GraphDisplaySpecifications = {
	properties: {
		id: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		node_label_field_name: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		node_icons: {
	type: 'any-of',
	contains: [{
	type: 'dictionary',
	contains: {
	type: 'string',
},
}, {
	type: 'null',
}],
},
	},
} as const;

export const $GraphElementFilter = {
	properties: {
		element_type_name: {
	type: 'string',
	isRequired: true,
},
		select: {
	type: 'FilterSelect',
	isRequired: true,
},
		filter_value: {
	type: 'RuleGroup',
	isRequired: true,
},
	},
} as const;

export const $HTTPValidationError = {
	properties: {
		detail: {
	type: 'array',
	contains: {
		type: 'ValidationError',
	},
},
	},
} as const;

export const $ItemCreate = {
	properties: {
		title: {
	type: 'string',
	isRequired: true,
},
		description: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
	},
} as const;

export const $ItemPublic = {
	properties: {
		title: {
	type: 'string',
	isRequired: true,
},
		description: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		id: {
	type: 'number',
	isRequired: true,
},
		owner_id: {
	type: 'number',
	isRequired: true,
},
	},
} as const;

export const $ItemUpdate = {
	properties: {
		title: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		description: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
	},
} as const;

export const $ItemsPublic = {
	properties: {
		data: {
	type: 'array',
	contains: {
		type: 'ItemPublic',
	},
	isRequired: true,
},
		count: {
	type: 'number',
	isRequired: true,
},
	},
} as const;

export const $Log = {
	description: `An ORM representation of log data.`,
	properties: {
		id: {
	type: 'string',
	format: 'uuid',
},
		created: {
	type: 'any-of',
	contains: [{
	type: 'string',
	format: 'date-time',
}, {
	type: 'null',
}],
},
		updated: {
	type: 'any-of',
	contains: [{
	type: 'string',
	format: 'date-time',
}, {
	type: 'null',
}],
},
		name: {
	type: 'string',
	description: `The logger name.`,
	isRequired: true,
},
		level: {
	type: 'number',
	description: `The log level.`,
	isRequired: true,
},
		message: {
	type: 'string',
	description: `The log message.`,
	isRequired: true,
},
		timestamp: {
	type: 'string',
	description: `The log timestamp.`,
	isRequired: true,
	format: 'date-time',
},
		flow_run_id: {
	type: 'any-of',
	description: `The flow run ID associated with the log.`,
	contains: [{
	type: 'string',
	format: 'uuid',
}, {
	type: 'null',
}],
},
		task_run_id: {
	type: 'any-of',
	description: `The task run ID associated with the log.`,
	contains: [{
	type: 'string',
	format: 'uuid',
}, {
	type: 'null',
}],
},
	},
} as const;

export const $Message = {
	properties: {
		message: {
	type: 'string',
	isRequired: true,
},
	},
} as const;

export const $NetworkXHitsSpecifications = {
	description: `Specifications on how to run NetworkX Hits algorithm on the graph and save result (i.e. authority and hub values)`,
	properties: {
		authority_property_name: {
	type: 'string',
	description: `The field to save authority in.`,
	isRequired: true,
},
		hub_property_name: {
	type: 'string',
	description: `The field to save hub in.`,
	isRequired: true,
},
		max_iter: {
	type: 'number',
	description: `Maximum number of iterations in power method.`,
	default: 100,
},
		tol: {
	type: 'number',
	description: `Error tolerance used to check convergence in power method iteration.`,
	default: 1e-8,
},
		normalized: {
	type: 'boolean',
	description: `Normalize results by the sum of all of the values.`,
	default: true,
},
	},
} as const;

export const $NetworkXPagerankSpecifications = {
	description: `Specifications on how to run NetworkX PageRank algorithm on the graph and save result (i.e. pagerank values)`,
	properties: {
		pagerank_property_name: {
	type: 'string',
	description: `The field to save pagerank in.`,
	isRequired: true,
},
		directed: {
	type: 'boolean',
	description: `Whether or not graph should be considered as directed while running the algorithm.`,
	isRequired: true,
},
		alpha: {
	type: 'number',
	description: `Damping parameter for PageRank.`,
	default: 0.85,
},
	},
} as const;

export const $NetworkXProcessorSpecifications = {
	properties: {
		algorithm_specifications: {
	type: 'any-of',
	contains: [{
	type: 'NetworkXPagerankSpecifications',
}, {
	type: 'NetworkXHitsSpecifications',
}],
	isRequired: true,
},
	},
} as const;

export const $NewPassword = {
	properties: {
		token: {
	type: 'string',
	isRequired: true,
},
		new_password: {
	type: 'string',
	isRequired: true,
},
	},
} as const;

export const $Node = {
	properties: {
		id: {
	type: 'string',
	isRequired: true,
},
		type: {
	type: 'string',
	isRequired: true,
},
		data: {
	type: 'dictionary',
	contains: {
	properties: {
	},
},
},
	},
} as const;

export const $NodeProperty = {
	properties: {
		name: {
	type: 'string',
	isRequired: true,
},
		type: {
	type: 'string',
	isRequired: true,
},
		is_primary_key: {
	type: 'boolean',
	default: false,
},
	},
} as const;

export const $NodeType = {
	properties: {
		name: {
	type: 'string',
	isRequired: true,
},
		properties: {
	type: 'array',
	contains: {
		type: 'NodeProperty',
	},
	isRequired: true,
},
	},
} as const;

export const $NumericPropertyInterval = {
	properties: {
		n: {
	type: 'number',
	description: `Number of cuts used to split values span.`,
	isRequired: true,
},
		min_max_counts: {
	type: 'array',
	contains: {
	type: 'unknown[]',
	maxItems: 3,
	minItems: 3,
},
	isRequired: true,
},
	},
} as const;

export const $NumericPropertyStatistics = {
	properties: {
		min: {
	properties: {
	},
	isRequired: true,
},
		max: {
	properties: {
	},
	isRequired: true,
},
		mean: {
	properties: {
	},
	isRequired: true,
},
		median: {
	properties: {
	},
	isRequired: true,
},
		std: {
	properties: {
	},
	isRequired: true,
},
		quantiles: {
	type: 'array',
	contains: {
		type: 'NumericPropertyInterval',
	},
	isRequired: true,
},
		bins: {
	type: 'array',
	contains: {
		type: 'NumericPropertyInterval',
	},
	isRequired: true,
},
	},
} as const;

export const $Relation = {
	properties: {
		source: {
	type: 'string',
	isRequired: true,
},
		target: {
	type: 'string',
	isRequired: true,
},
		type: {
	type: 'string',
	isRequired: true,
},
		data: {
	type: 'dictionary',
	contains: {
	properties: {
	},
},
},
	},
} as const;

export const $RelationProperty = {
	properties: {
		name: {
	type: 'string',
	isRequired: true,
},
		type: {
	type: 'string',
	isRequired: true,
},
	},
} as const;

export const $RelationType = {
	properties: {
		name: {
	type: 'string',
	isRequired: true,
},
		properties: {
	type: 'array',
	contains: {
		type: 'RelationProperty',
	},
	isRequired: true,
},
	},
} as const;

export const $Rule = {
	properties: {
		field: {
	type: 'string',
	isRequired: true,
},
		operator: {
	type: 'string',
	isRequired: true,
},
		value: {
	properties: {
	},
	isRequired: true,
},
	},
} as const;

export const $RuleCombinator = {
	type: 'Enum',
	enum: ['and',],
} as const;

export const $RuleGroup = {
	properties: {
		combinator: {
	type: 'RuleCombinator',
	isRequired: true,
},
		rules: {
	type: 'array',
	contains: {
		type: 'Rule',
	},
	default: [],
},
	},
} as const;

export const $StateType = {
	type: 'Enum',
	enum: ['SCHEDULED','PENDING','RUNNING','COMPLETED','FAILED','CANCELLED','CRASHED','PAUSED','CANCELLING',],
} as const;

export const $StixDatasetSpecifications = {
	properties: {
		files_content: {
	type: 'array',
	contains: {
	type: 'string',
	format: 'data-url',
},
	isRequired: true,
},
	},
} as const;

export const $SymbolicPropertyStatistics = {
	properties: {
		value_counts_max: {
	type: 'any-of',
	description: `Maximum number of items which have been saved in value_counts; if None, value_counts is untouched.`,
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
	isRequired: true,
},
		value_counts: {
	type: 'array',
	contains: {
	type: 'unknown[]',
	maxItems: 2,
	minItems: 2,
},
	isRequired: true,
},
	},
} as const;

export const $Token = {
	properties: {
		access_token: {
	type: 'string',
	isRequired: true,
},
		token_type: {
	type: 'string',
	default: 'bearer',
},
	},
} as const;

export const $UpdatePassword = {
	properties: {
		current_password: {
	type: 'string',
	isRequired: true,
},
		new_password: {
	type: 'string',
	isRequired: true,
},
	},
} as const;

export const $UserCreate = {
	properties: {
		email: {
	type: 'string',
	isRequired: true,
},
		is_active: {
	type: 'boolean',
	default: true,
},
		is_superuser: {
	type: 'boolean',
	default: false,
},
		full_name: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		password: {
	type: 'string',
	isRequired: true,
},
	},
} as const;

export const $UserPublic = {
	properties: {
		email: {
	type: 'string',
	isRequired: true,
},
		is_active: {
	type: 'boolean',
	default: true,
},
		is_superuser: {
	type: 'boolean',
	default: false,
},
		full_name: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		id: {
	type: 'number',
	isRequired: true,
},
	},
} as const;

export const $UserRegister = {
	properties: {
		email: {
	type: 'string',
	isRequired: true,
},
		password: {
	type: 'string',
	isRequired: true,
},
		full_name: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
	},
} as const;

export const $UserUpdate = {
	properties: {
		email: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		is_active: {
	type: 'boolean',
	default: true,
},
		is_superuser: {
	type: 'boolean',
	default: false,
},
		full_name: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		password: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
	},
} as const;

export const $UserUpdateMe = {
	properties: {
		full_name: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		email: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
	},
} as const;

export const $UsersPublic = {
	properties: {
		data: {
	type: 'array',
	contains: {
		type: 'UserPublic',
	},
	isRequired: true,
},
		count: {
	type: 'number',
	isRequired: true,
},
	},
} as const;

export const $ValidationError = {
	properties: {
		loc: {
	type: 'array',
	contains: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'number',
}],
},
	isRequired: true,
},
		msg: {
	type: 'string',
	isRequired: true,
},
		type: {
	type: 'string',
	isRequired: true,
},
	},
} as const;

export const $WorkflowContent = {
	properties: {
		metadata: {
	type: 'WorkflowPublic',
	isRequired: true,
},
		logs: {
	type: 'array',
	contains: {
		type: 'Log',
	},
	isRequired: true,
},
	},
} as const;

export const $WorkflowPublic = {
	properties: {
		created_at: {
	type: 'any-of',
	contains: [{
	type: 'string',
	format: 'date-time',
}, {
	type: 'null',
}],
},
		updated_at: {
	type: 'any-of',
	contains: [{
	type: 'string',
	format: 'date-time',
}, {
	type: 'null',
}],
},
		type: {
	type: 'WorkflowType',
	isRequired: true,
},
		description: {
	type: 'string',
	isRequired: true,
},
		state: {
	type: 'StateType',
	isRequired: true,
},
		started_at: {
	type: 'any-of',
	description: `Timestamp when the workflow started (can be different from \`created_at\`).`,
	contains: [{
	type: 'string',
	format: 'date-time',
}, {
	type: 'null',
}],
},
		ended_at: {
	type: 'any-of',
	description: `Timestamp when the workflow ended.`,
	contains: [{
	type: 'string',
	format: 'date-time',
}, {
	type: 'null',
}],
},
		id: {
	type: 'number',
	isRequired: true,
},
		owner_id: {
	type: 'number',
	isRequired: true,
},
		related_dataset_id: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
	isRequired: true,
},
	},
} as const;

export const $WorkflowType = {
	type: 'Enum',
	enum: ['build_dataset','run_processor',],
} as const;

export const $WorkflowsPublic = {
	properties: {
		data: {
	type: 'array',
	contains: {
		type: 'WorkflowPublic',
	},
	isRequired: true,
},
		count: {
	type: 'number',
	isRequired: true,
},
	},
} as const;