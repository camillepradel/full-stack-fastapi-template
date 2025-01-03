import { DatasetPublic, FilterSelect, GraphElementFilter, NodeType, RuleGroup } from "../../client";
import { Card, CardBody, Checkbox, Code, Flex, Stack, Tag, Text, Tooltip } from '@chakra-ui/react';
import { defaultOperators, Field, QueryBuilder, RuleGroupType, type RuleType, formatQuery } from 'react-querybuilder';
import { QueryBuilderChakra } from '@react-querybuilder/chakra';
import 'react-querybuilder/dist/query-builder.css';
import { EditIcon } from "@chakra-ui/icons";


interface TypeFilterProps {
  node_type: NodeType;
  nodeFilters: GraphElementFilter[];
  setNodeFilters: (nodeFilters: GraphElementFilter[]) => void;
}


function ruleGroupToQuery(ruleGroup: RuleGroup): RuleGroupType {
  return {
    combinator: ruleGroup.combinator,
    rules: (ruleGroup.rules ?? []).map((rule) => {
      return {
        field: rule.field,
        operator: rule.operator,
        value: rule.value,
      }
    }),
  }
}


function queryToRuleGroup(query: RuleGroupType): RuleGroup {
  const ruleGroup: RuleGroup = {
    combinator: query.combinator === "and"? "and": "and",
    rules: query.rules.map((rule) => {
      if ('field' in rule && 'operator' in rule && 'value' in rule) {
        // always the case since groups are not allowed
        return {
          field: rule.field,
          operator: rule.operator,
          value: rule.value,
        }
      } else {
        throw new Error("Invalid rule")
      }
    })}
  return ruleGroup
}

const TypeFilter = ({ node_type, nodeFilters, setNodeFilters }: TypeFilterProps) => {

  const fields: Field[] = node_type.properties.map((property) => {
    let field: Field = {
      name: property.name,
      label: property.name,
    }
    if (property.type === "STRING") {
      field.operators = defaultOperators.filter((op) => ['=', '!=', 'contains'].includes(op.name) )
    } else if (property.type === "BOOL") {
      field.valueEditorType = 'checkbox'
      field.operators = defaultOperators.filter((op) => op.name === '=')
      field.defaultValue = false
    } else if (["INT8", "INT16", "INT32", "INT64", "INT128", "UINT8", "UINT16", "UINT32", "UINT64", "FLOAT", "DOUBLE", "DECIMAL"].includes(property.type)) {
      field.inputType = 'number'
      field.operators = defaultOperators.filter((op) => ['=', '!=', '<', '>', '<=', '>='].includes(op.name))
      field.validator = (r: RuleType) => !!r.value
    }
    return field
  })

  const filterIndex = nodeFilters.findIndex(filter => filter.element_type_name === node_type.name);
  const selectValue = nodeFilters[filterIndex].select
  const query: RuleGroupType = ruleGroupToQuery(nodeFilters[filterIndex].filter_value)

  return (
    <>
      <Flex >
        <Checkbox
          isChecked={selectValue === "everything"}
          isIndeterminate={selectValue === "custom"}
          onChange={e => setNodeFilters([
            ...nodeFilters.slice(0, filterIndex),
            { ...nodeFilters[filterIndex], select: e.target.checked ? "everything" : "nothing" },
            ...nodeFilters.slice(filterIndex + 1)])}
        >
          {node_type.name}
        </Checkbox>
        {selectValue==="everything" && <Text ml="10px" fontSize='xs'>Select all</Text>}
        {selectValue==="nothing" && <Text ml="10px" fontSize='xs'>Ignore all</Text>}
        {selectValue==="custom" && <Text ml="10px" fontSize='xs'>Custom select</Text>}
        {selectValue!="custom" && <EditIcon ml="10px" onClick={() => setNodeFilters([
            ...nodeFilters.slice(0, filterIndex),
            { ...nodeFilters[filterIndex], select: "custom" },
            ...nodeFilters.slice(filterIndex + 1)])} />}
      </Flex>

      {
        selectValue==="custom" &&
        <QueryBuilderChakra>
          <QueryBuilder
            fields={fields}
            query={query}
            onQueryChange={(query) => setNodeFilters([
              ...nodeFilters.slice(0, filterIndex),
              { ...nodeFilters[filterIndex], filter_value: queryToRuleGroup(query) },
              ...nodeFilters.slice(filterIndex + 1)])}
            controlElements={{
              // prevent creation of groups (not handled by backend)
              addGroupAction: () => null,
              // do not allow to select combinator (not handled by backend)
              combinatorSelector: () => null,
            }}
            controlClassnames={{ queryBuilder: 'queryBuilder-branches' }}
          />
        </QueryBuilderChakra>
      }
    </>
  )
}

interface FiltersDescriptionProps {
  nodeFilters: GraphElementFilter[];
}

const FiltersDescription = ({ nodeFilters }: FiltersDescriptionProps) => {
  const notTotallySelectedNodeFilters = nodeFilters.filter(nodeFilter => nodeFilter.select === "custom" || nodeFilter.select === "nothing");

  return (
    <Card>
      <CardBody py="10px">
        {notTotallySelectedNodeFilters.length === 0 && <Code>Select all nodes</Code>}
      {notTotallySelectedNodeFilters.map(nodeFilter => (
          nodeFilter.select === "custom" &&
          <Tooltip key={nodeFilter.element_type_name} label={formatQuery(ruleGroupToQuery(nodeFilter.filter_value), 'spel')}><Tag><Text fontSize='xs'>[custom filter] </Text> {nodeFilter.element_type_name}</Tag></Tooltip>
      ))}
      {notTotallySelectedNodeFilters.map(nodeFilter => (
          nodeFilter.select === "nothing" &&
          <Tag key={nodeFilter.element_type_name} mx="4px"><s>{nodeFilter.element_type_name}</s></Tag>
      ))}
      </CardBody>
    </Card>
  )
}


interface DatasetFiltersProps {
  dataset: DatasetPublic;
  nodeFilters: GraphElementFilter[];
  setNodeFilters: (nodeFilters: GraphElementFilter[]) => void;
  initNodeFilters: (node_types: NodeType[], initValue: FilterSelect) => GraphElementFilter[];
}

const DatasetFilters = ({ dataset, nodeFilters, setNodeFilters, initNodeFilters }: DatasetFiltersProps) => {

  const nodesRootNodeChecked = Object.values(nodeFilters).every(filter => filter.select === "everything");
  const nodesRootNodeIndeterminate = Object.values(nodeFilters).some(filter => filter.select === "custom" || filter.select === "everything") && !nodesRootNodeChecked;


  return (
    <>
      <Flex >
        <Checkbox
          isChecked={nodesRootNodeChecked}
          isIndeterminate={nodesRootNodeIndeterminate}
          onChange={e => setNodeFilters(initNodeFilters(dataset.dataset_schema?.node_types ?? [], e.target.checked ? "everything" : "nothing"))}
        >
          Nodes
        </Checkbox>
        {nodesRootNodeChecked && <Text ml="10px" fontSize='xs'>Select all</Text>}
        {!nodesRootNodeChecked && !nodesRootNodeIndeterminate && <Text ml="10px" fontSize='xs'>Ignore all - <b>Nothing will be displayed!</b></Text>}
        {nodesRootNodeIndeterminate && <Text ml="10px" fontSize='xs'>Some constraints defined below</Text>}
      </Flex>
      <Stack pl={6} mt={1} spacing={1}>
        {dataset.dataset_schema?.node_types.map((node_type) => (
          <TypeFilter key={node_type.name} node_type={node_type} nodeFilters={nodeFilters} setNodeFilters={setNodeFilters} />
        ))}
      </Stack>

      <FiltersDescription nodeFilters={nodeFilters} />

    </>
  )
}

export default DatasetFilters;
