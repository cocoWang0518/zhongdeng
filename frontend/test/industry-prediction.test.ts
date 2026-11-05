import { shallowMount } from '@vue/test-utils'
import { NDataTable, NSelect } from 'naive-ui'
import { describe, expect, it } from 'vitest'
import { nextTick } from 'vue'
import PredictForm from '../src/components/PredictForm.vue'
import RiskTabPane from '../src/components/tabs/RiskTabPane.vue'

describe('行业预测表单', () => {
  it('只提供11个行业，并随行业排除不支持的数据组合', async () => {
    const wrapper = shallowMount(PredictForm, {
      props: { data: { task_type: '', data_type: '', industry_type: '' } },
      global: { renderStubDefaultSlot: true },
    })
    const selects = wrapper.findAllComponents(NSelect)
    const industries = selects[0].props('options') as { value: string }[]
    expect(industries).toHaveLength(11)
    expect(industries.map(item => item.value)).not.toContain('医疗健康产业')
    expect(wrapper.find('n-tabs-stub').exists()).toBe(false)
    selects[0].vm.$emit('update:value', '银行')
    await nextTick()
    expect(selects[1].props('options')).toHaveLength(2)
    selects[1].vm.$emit('update:value', '仅财务')
    selects[0].vm.$emit('update:value', '工业设备制造')
    await nextTick()
    expect(selects[1].props('options')).toEqual([{ label: '财务+非财务', value: '财务+非财务' }])
    expect(selects[1].props('value')).toBe('')
    selects[0].vm.$emit('update:value', '科技产业')
    await nextTick()
    expect(selects[1].props('options')).toHaveLength(1)
    selects[0].vm.$emit('update:value', null)
    await nextTick()
    expect(selects[1].props('disabled')).toBe(true)
  })

  it('回填历史参数时清除已排除的组合', () => {
    const wrapper = shallowMount(PredictForm, {
      props: { data: { task_type: '信用债项评级', data_type: '仅财务', industry_type: '科技产业' } },
      global: { renderStubDefaultSlot: true },
    })
    expect(wrapper.findAllComponents(NSelect)[1].props('value')).toBe('')
  })
})

describe('指标读取', () => {
  it('保留零召回率并把逐评级报告交给表格', () => {
    const report = [{ '类别': 'AA', '精确率': 0, '召回率': 0, 'F1 得分': 0, '样本数': 2 }]
    const wrapper = shallowMount(RiskTabPane, {
      props: { riskText: { '准确率': 0.75, '精确率': 0.6, '召回率': 0.75, 'F1 得分': 0.65, '分类报告': report }, riskExplain: {}, industryRiskAnalysisColumns: [] },
      global: { renderStubDefaultSlot: true },
    })
    expect(wrapper.text()).toContain('0.75')
    expect(wrapper.findComponent(NDataTable).props('data')).toEqual(report)
  })
})
