import { flushPromises, shallowMount } from '@vue/test-utils'
import { NDataTable } from 'naive-ui'
import { expect, it, vi } from 'vitest'
import QueryResult from '../src/components/QueryResult.vue'

const mocks = vi.hoisted(() => ({ post: vi.fn() }))
vi.mock('../src/utils/request', () => ({ default: { post: mocks.post } }))

it('查询请求9个月趋势图，保留完整历史评级表', async () => {
  mocks.post.mockResolvedValue({ data: { status: 'success', data: { trend_image: 'data:image/png;base64,test' } } })
  const history = Array.from({ length: 12 }, (_, index) => ({ 时间: `2025-${String(index + 1).padStart(2, '0')}`, GBDT: 'AA' }))
  const wrapper = shallowMount(QueryResult, {
    props: { data: { bond_type: '城投债', identifier_data: { 债券代码: '1080172', 债券名称: '测试债券', 时间: '2025-12' }, df_results: [], df_history: history } },
    global: { renderStubDefaultSlot: true, stubs: { Card: { template: '<div><slot name="header-extra" /><slot /></div>' } } },
  })
  await flushPromises()
  expect(mocks.post).toHaveBeenCalledWith('/ketiyi/trend', expect.objectContaining({ months: 9, df_history: history }), expect.anything())
  expect(wrapper.text()).toContain('近 9 个月走势')
  expect(wrapper.findAllComponents(NDataTable).some(table => table.props('data')?.length === 12)).toBe(true)
  wrapper.unmount()
})
