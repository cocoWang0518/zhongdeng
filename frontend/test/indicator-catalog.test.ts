import type { VNode } from 'vue'
import { flushPromises, shallowMount } from '@vue/test-utils'
import { NDataTable, NInput, NSelect } from 'naive-ui'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, reactive } from 'vue'
import Indicators from '../src/pages/indicators.vue'

const mocks = vi.hoisted(() => ({ get: vi.fn(), replace: vi.fn(), route: {} as { query: Record<string, string> } }))
vi.mock('../src/utils/request', () => ({ default: { get: mocks.get } }))
vi.mock('vue-router', () => ({ useRoute: () => mocks.route, useRouter: () => ({ replace: mocks.replace }) }))

const categories = ['非金融主体', '非金融债', '城投主体', '城投债', '银行主体', '银行债', '保险主体', '保险债', '证券主体', '证券公司债', '信托主体', '信托公司债', '资产管理产品', '信贷类ABS', '场内基金管理人主体']
const rows = [
  { id: 1, index: 1, feature_name: 'AF1', actual_meaning: '产品登记编码', data_source: '中国理财网', feature_category: '基础信息', calculation_method: '产品唯一编码', used_model: '资产管理产品' },
  { id: 2, index: 2, feature_name: 'M1', actual_meaning: 'GDP', data_source: 'Wind数据库', feature_category: '宏观因子', calculation_method: '无需计算', used_model: '资产管理产品' },
]

beforeEach(() => {
  vi.clearAllMocks()
  mocks.route = reactive({ query: { model: '资产管理产品' } })
  mocks.get.mockResolvedValue({ data: { status: 'success', selected_model: '资产管理产品', models: categories.map(value => ({ label: value, value, count: value === '资产管理产品' ? 194 : 0 })), total: 194, items: rows } })
})

describe('指标查看', () => {
  it('数据库与文件分类使用同一表格，保留15类顺序、计数、搜索和分页', async () => {
    const wrapper = shallowMount(Indicators, { global: { renderStubDefaultSlot: true } })
    await flushPromises()
    const select = wrapper.findComponent(NSelect)
    const options = select.props('options') as { label: string, value: string }[]
    expect(options.map(option => option.value)).toEqual(categories)
    expect(options.find(option => option.value === '资产管理产品')?.label).toBe('资产管理产品（194）')
    expect(wrapper.text()).toContain('共 194 个指标')
    const table = wrapper.findComponent(NDataTable)
    expect((table.props('columns') || []).map(column => 'title' in column ? column.title : undefined)).toEqual(['序号', '特征名', '实际含义', '特征类型', '计算方式/说明', '数据来源'])
    const pagination = table.props('pagination')
    expect(pagination && pagination.defaultPageSize).toBe(15)
    expect(table.props('data')).toEqual(rows)
    wrapper.findComponent(NInput).vm.$emit('update:value', '理财网')
    await nextTick()
    expect(table.props('data')).toEqual([rows[0]])
    select.vm.$emit('update:value', '银行债')
    expect(mocks.replace).toHaveBeenCalledWith({ path: '/indicators', query: { model: '银行债' } })
    wrapper.unmount()
  })

  it('旧分类链接切换到对应新分类', async () => {
    mocks.route.query.model = 'ABS模型'
    const wrapper = shallowMount(Indicators, { global: { renderStubDefaultSlot: true } })
    await flushPromises()
    expect(mocks.replace).toHaveBeenCalledWith({ path: '/indicators', query: { model: '信贷类ABS' } })
    wrapper.unmount()
  })

  it('原始资料为空时显示未提供，已核实的单位与公式原样显示', async () => {
    const missing = { ...rows[0], feature_name: 'M2', actual_meaning: '工业增加值同比', calculation_method: null, calculation_method_status: 'not_provided' }
    const unverified = { ...missing, calculation_method_status: 'unverified' }
    const verified = { ...rows[1], calculation_method: '单位: 亿元', calculation_method_status: 'verified' }
    mocks.get.mockResolvedValue({ data: { status: 'success', selected_model: '资产管理产品', models: [], total: 3, items: [missing, unverified, verified] } })
    const wrapper = shallowMount(Indicators, { global: { renderStubDefaultSlot: true } })
    await flushPromises()
    const columns = wrapper.findComponent(NDataTable).props('columns') as { key: string, render?: (row: Record<string, unknown>, index: number) => VNode }[]
    const column = columns.find(item => item.key === 'calculation_method')
    if (!column?.render)
      throw new Error('Missing calculation renderer')
    expect(column.render(missing, 0).children).toBe('未提供')
    expect(column.render(unverified, 1).props?.title).toContain('尚未找到可核实')
    expect(column.render(verified, 2).children).toBe('单位: 亿元')
    wrapper.findComponent(NInput).vm.$emit('update:value', '未提供')
    await nextTick()
    expect(wrapper.findComponent(NDataTable).props('data')).toHaveLength(2)
    wrapper.unmount()
  })
})
