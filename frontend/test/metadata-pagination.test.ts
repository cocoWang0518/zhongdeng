import { flushPromises, mount } from '@vue/test-utils'
import { NInput, NPagination } from 'naive-ui'
import { beforeEach, expect, it, vi } from 'vitest'
import { nextTick, reactive } from 'vue'
import Assets from '../src/pages/assets.vue'
import Indicators from '../src/pages/indicators.vue'

const mocks = vi.hoisted(() => ({ get: vi.fn(), replace: vi.fn(), route: {} as { query: Record<string, string> } }))
vi.mock('../src/utils/request', () => ({ default: { get: mocks.get } }))
vi.mock('vue-router', () => ({ useRoute: () => mocks.route, useRouter: () => ({ replace: mocks.replace }) }))

beforeEach(() => {
  vi.clearAllMocks()
})

for (const [title, Page, model] of [['指标查看', Indicators, '非金融主体'], ['资产查看', Assets, '信用债模型']] as const) {
  it(`${title}实际显示15/10/30/50条，切换后仍可翻页和搜索`, async () => {
    mocks.route = reactive({ query: { model } })
    const items = Array.from({ length: 83 }, (_, index) => ({
      id: index + 1, index: index + 1,
      feature_name: `F${index + 1}`, actual_meaning: `测试指标${index + 1}`,
      data_source: '测试数据', feature_category: '财务', calculation_method: '测试说明', used_model: model,
      资产代码: String(index + 1), 资产名称: `测试资产${index + 1}`, 适用模型: model,
    }))
    mocks.get.mockResolvedValue({ data: { status: 'success', selected_model: model, total: 83, items, models: [{ label: model, value: model, count: 83 }] } })
    const wrapper = mount(Page)
    await flushPromises()
    const rowCount = () => wrapper.findAll('tbody tr').length
    expect(rowCount()).toBe(15)
    for (const size of [10, 30, 50, 15]) {
      wrapper.findComponent(NPagination).vm.$emit('update:pageSize', size)
      await nextTick()
      expect(rowCount()).toBe(size)
      expect(wrapper.findComponent(NPagination).props('pageSize')).toBe(size)
    }
    wrapper.findComponent(NPagination).vm.$emit('update:page', 2)
    await nextTick()
    expect(rowCount()).toBe(15)
    expect(wrapper.find('tbody tr td').text()).toBe('16')
    // 在后续页改变每页条数，末页也应按照新条数正确显示。
    wrapper.findComponent(NPagination).vm.$emit('update:pageSize', 30)
    await nextTick()
    expect(rowCount()).toBe(30)
    wrapper.findComponent(NPagination).vm.$emit('update:page', 3)
    await nextTick()
    expect(rowCount()).toBe(23)
    wrapper.findComponent(NInput).vm.$emit('update:value', '测试')
    await nextTick()
    expect(wrapper.findComponent(NPagination).props('pageSize')).toBe(30)
    expect(rowCount()).toBe(23)
    wrapper.unmount()
  })
}
