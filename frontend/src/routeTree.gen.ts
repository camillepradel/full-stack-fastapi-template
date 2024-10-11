/* prettier-ignore-start */

/* eslint-disable */

// @ts-nocheck

// noinspection JSUnusedGlobalSymbols

// This file is auto-generated by TanStack Router

// Import Routes

import { Route as rootRoute } from './routes/__root'
import { Route as ResetPasswordImport } from './routes/reset-password'
import { Route as RecoverPasswordImport } from './routes/recover-password'
import { Route as LoginImport } from './routes/login'
import { Route as LayoutImport } from './routes/_layout'
import { Route as LayoutIndexImport } from './routes/_layout/index'
import { Route as LayoutSettingsImport } from './routes/_layout/settings'
import { Route as LayoutItemsImport } from './routes/_layout/items'
import { Route as LayoutGraphd3Import } from './routes/_layout/graph_d3'
import { Route as LayoutGraphcytoscapeImport } from './routes/_layout/graph_cytoscape'
import { Route as LayoutDatasetssImport } from './routes/_layout/datasetss'
import { Route as LayoutDatasetsImport } from './routes/_layout/datasets'
import { Route as LayoutAdminImport } from './routes/_layout/admin'

// Create/Update Routes

const ResetPasswordRoute = ResetPasswordImport.update({
  path: '/reset-password',
  getParentRoute: () => rootRoute,
} as any)

const RecoverPasswordRoute = RecoverPasswordImport.update({
  path: '/recover-password',
  getParentRoute: () => rootRoute,
} as any)

const LoginRoute = LoginImport.update({
  path: '/login',
  getParentRoute: () => rootRoute,
} as any)

const LayoutRoute = LayoutImport.update({
  id: '/_layout',
  getParentRoute: () => rootRoute,
} as any)

const LayoutIndexRoute = LayoutIndexImport.update({
  path: '/',
  getParentRoute: () => LayoutRoute,
} as any)

const LayoutSettingsRoute = LayoutSettingsImport.update({
  path: '/settings',
  getParentRoute: () => LayoutRoute,
} as any)

const LayoutItemsRoute = LayoutItemsImport.update({
  path: '/items',
  getParentRoute: () => LayoutRoute,
} as any)

const LayoutGraphd3Route = LayoutGraphd3Import.update({
  path: '/graph_d3',
  getParentRoute: () => LayoutRoute,
} as any)

const LayoutGraphcytoscapeRoute = LayoutGraphcytoscapeImport.update({
  path: '/graph_cytoscape',
  getParentRoute: () => LayoutRoute,
} as any)

const LayoutDatasetssRoute = LayoutDatasetssImport.update({
  path: '/datasetss',
  getParentRoute: () => LayoutRoute,
} as any)

const LayoutDatasetsRoute = LayoutDatasetsImport.update({
  path: '/datasets',
  getParentRoute: () => LayoutRoute,
} as any)

const LayoutAdminRoute = LayoutAdminImport.update({
  path: '/admin',
  getParentRoute: () => LayoutRoute,
} as any)

// Populate the FileRoutesByPath interface

declare module '@tanstack/react-router' {
  interface FileRoutesByPath {
    '/_layout': {
      preLoaderRoute: typeof LayoutImport
      parentRoute: typeof rootRoute
    }
    '/login': {
      preLoaderRoute: typeof LoginImport
      parentRoute: typeof rootRoute
    }
    '/recover-password': {
      preLoaderRoute: typeof RecoverPasswordImport
      parentRoute: typeof rootRoute
    }
    '/reset-password': {
      preLoaderRoute: typeof ResetPasswordImport
      parentRoute: typeof rootRoute
    }
    '/_layout/admin': {
      preLoaderRoute: typeof LayoutAdminImport
      parentRoute: typeof LayoutImport
    }
    '/_layout/datasets': {
      preLoaderRoute: typeof LayoutDatasetsImport
      parentRoute: typeof LayoutImport
    }
    '/_layout/datasetss': {
      preLoaderRoute: typeof LayoutDatasetssImport
      parentRoute: typeof LayoutImport
    }
    '/_layout/graph_cytoscape': {
      preLoaderRoute: typeof LayoutGraphcytoscapeImport
      parentRoute: typeof LayoutImport
    }
    '/_layout/graph_d3': {
      preLoaderRoute: typeof LayoutGraphd3Import
      parentRoute: typeof LayoutImport
    }
    '/_layout/items': {
      preLoaderRoute: typeof LayoutItemsImport
      parentRoute: typeof LayoutImport
    }
    '/_layout/settings': {
      preLoaderRoute: typeof LayoutSettingsImport
      parentRoute: typeof LayoutImport
    }
    '/_layout/': {
      preLoaderRoute: typeof LayoutIndexImport
      parentRoute: typeof LayoutImport
    }
  }
}

// Create and export the route tree

export const routeTree = rootRoute.addChildren([
  LayoutRoute.addChildren([
    LayoutAdminRoute,
    LayoutDatasetsRoute,
    LayoutDatasetssRoute,
    LayoutGraphcytoscapeRoute,
    LayoutGraphd3Route,
    LayoutItemsRoute,
    LayoutSettingsRoute,
    LayoutIndexRoute,
  ]),
  LoginRoute,
  RecoverPasswordRoute,
  ResetPasswordRoute,
])

/* prettier-ignore-end */
