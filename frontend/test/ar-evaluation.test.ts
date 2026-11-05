import { flushPromises, shallowMount } from '@vue/test-utils'
import { NButton, NDataTable, NModal, NSwitch, NUpload } from 'naive-ui'
import { beforeEach, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import ArEvaluation from '../src/components/ArEvaluation.vue'
import NewPrediction from '../src/pages/new.vue'

const mocks = vi.hoisted(() => ({ post: vi.fn() }))
vi.mock('../src/utils/request', () => ({ default: { post: mocks.post } }))
vi.mock('../src/stores/sidebar', () => ({ useSidebarStore: () => ({ chatSessions: [] }) }))
vi.mock('vue-router', () => ({ useRouter: () => ({ push: vi.fn() }) }))

const responseData = {
  summary: { overall_ar: 0, overall_method: '有效月份AR等权平均', valid_months: 1, total_months: 2, sample_count: 4, subject_count: 2, data_end: '2025-09-01', mean_auc: 0.5 },
  monthly: [
    { month: '2023-01', N: 2, N_default_1y: 1, N_nondefault_1y: 1, AR_CAP: 0, AUC: 0.5, valid_AR: true, reason: '' },
    { month: '2023-02', N: 2, N_default_1y: 0, N_nondefault_1y: 2, AR_CAP: null, AUC: null, valid_AR: false, reason: '当月无未来一年违约样本' },
  ],
  warnings: [],
  cleaning: { input_rows: 4, missing_rows: 0, duplicate_rows: 0, already_defaulted_rows: 0, incomplete_window_rows: 0 },
}

beforeEach(() => vi.clearAllMocks())

it('新建预测标题旁按钮打开AR弹窗，原预测表单保留', async () => {
  const wrapper = shallowMount(NewPrediction, {
    global: { renderStubDefaultSlot: true, stubs: { Card: { template: '<div><slot name="header-extra" /><slot /></div>' } } },
  })
  expect(wrapper.findComponent({ name: 'PredictForm' }).exists()).toBe(true)
  expect(wrapper.findComponent(ArEvaluation).exists()).toBe(false)
  const button = wrapper.findAllComponents(NButton).find(item => item.text().includes('模型AR值'))!
  expect(button).toBeDefined()
  button.vm.$emit('click')
  await nextTick()
  expect(wrapper.findAllComponents(NModal)[0].props('show')).toBe(true)
  expect(wrapper.findComponent(ArEvaluation).exists()).toBe(true)
  wrapper.unmount()
})

it('上传评级文件计算AR，保留0值，默认展示有效月并可查看无效原因', async () => {
  mocks.post.mockResolvedValue({ data: { status: 'success', data: responseData } })
  const wrapper = shallowMount(ArEvaluation, { global: { renderStubDefaultSlot: true } })
  const file = new File(['stkcd,ym,信用评级,首次违约日期'], 'rating.csv', { type: 'text/csv' })
  wrapper.findComponent(NUpload).vm.$emit('change', { fileList: [{ id: '1', name: file.name, status: 'finished', file }] })
  await nextTick()
  const button = wrapper.findAllComponents(NButton).find(item => item.text().includes('计算AR值'))!
  button.vm.$emit('click')
  await flushPromises()
  expect(mocks.post).toHaveBeenCalledTimes(1)
  const [url, payload] = mocks.post.mock.calls[0]
  expect(url).toBe('/ar/calculate')
  expect(payload.get('file')).toBe(file)
  expect(payload.get('data_end')).toBe('2025-09-01')
  expect(payload.get('rating_col')).toBe('信用评级')
  expect(wrapper.findComponent(NDataTable).props('data')).toHaveLength(1)
  const arColumn = (wrapper.findComponent(NDataTable).props('columns') || []).find(column => 'key' in column && column.key === 'AR_CAP') as unknown as { render: (row: typeof responseData.monthly[number]) => string }
  expect(arColumn.render(responseData.monthly[0])).toBe('0.000000')
  expect(arColumn.render(responseData.monthly[1])).toBe('无法计算')
  wrapper.findComponent(NSwitch).vm.$emit('update:value', false)
  await nextTick()
  expect(wrapper.findComponent(NDataTable).props('data')).toHaveLength(2)
  wrapper.findComponent(NUpload).vm.$emit('change', { fileList: [] })
  await nextTick()
  expect(wrapper.findComponent(NDataTable).exists()).toBe(false)
  wrapper.unmount()
})

it('未上传文件时提示，后端错误原样展示', async () => {
  const wrapper = shallowMount(ArEvaluation, { global: { renderStubDefaultSlot: true } })
  const button = wrapper.findAllComponents(NButton).find(item => item.text().includes('计算AR值'))!
  button.vm.$emit('click')
  await nextTick()
  expect(wrapper.text()).toContain('请先上传评级结果文件')
  expect(mocks.post).not.toHaveBeenCalled()
  const file = new File(['test'], 'rating.csv')
  wrapper.findComponent(NUpload).vm.$emit('change', { fileList: [{ id: '1', name: file.name, status: 'finished', file }] })
  await nextTick()
  mocks.post.mockRejectedValue({ response: { data: { message: '缺少必要字段：首次违约日期' } } })
  button.vm.$emit('click')
  await flushPromises()
  expect(wrapper.text()).toContain('缺少必要字段：首次违约日期')
  expect(wrapper.findComponent(NDataTable).exists()).toBe(false)
  wrapper.unmount()
})
