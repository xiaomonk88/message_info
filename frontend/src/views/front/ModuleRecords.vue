<template>
  <div class="page is-fluid" v-loading="loading && !firstLoad">
    <template v-if="module">
      <!-- OVH 晴空渐变页头横幅（精确复刻 Dedicated servers 顶栏） -->
      <PageHeader
        :title="module.name"
        :eyebrow="categoryName"
        :subtitle="module.description || '查看、筛选并管理当前数据板块下的所有结构化记录'"
      >
        <template #links>
          <span v-if="!isAdmin" class="badge text-bg-primary">
            {{ module.access.scope === 'all' ? '全部记录' : '我的与共享记录' }}
          </span>
          <button v-if="isAdmin" type="button" @click="trashDrawer = true">
            <Trash2 />回收站<template v-if="trash.total > 0"> ({{ trash.total }})</template>
          </button>
          <RouterLink v-if="isAdmin" to="/admin/modules">
            <Settings2 />字段配置
          </RouterLink>
        </template>
      </PageHeader>

      <!-- 未配置字段提示 -->
      <div v-if="!module.fields.length" class="panel">
        <div class="empty-state" style="min-height: 280px">
          <ListTree />
          <div class="empty-state-title">该板块尚未配置字段</div>
          <p>请前往「数据建模」为该板块关联所需字段，即可开始录入记录。</p>
          <button v-if="isAdmin" class="btn btn-primary" @click="$router.push('/admin/modules')">
            <Settings2 />去配置字段
          </button>
        </div>
      </div>

      <!-- OVH 外置操作栏（左：钴蓝主按钮 + 批量操作；右：搜索 + 视图 + 筛选） -->
      <template v-else>
        <div class="ovh-toolbar">
          <div class="toolbar-group">
            <button v-if="module.access.can_create" class="btn btn-primary" @click="openEdit()">
              <Plus />新增记录
            </button>

            <template v-if="isAdmin">
              <div class="ovh-dd">
                <button
                  class="btn btn-outline-secondary"
                  type="button"
                  :disabled="!selectedIds.length"
                  @click="bulkMenuOpen = !bulkMenuOpen"
                >
                  批量操作 ({{ selectedIds.length }})
                </button>
                <div v-if="bulkMenuOpen && selectedIds.length" class="dropdown-menu show ovh-dd-menu">
                  <button class="dropdown-item" type="button" @click="bulkMenuOpen = false; openAssign('share')">
                    <UserPlus />分配给用户
                  </button>
                  <button class="dropdown-item" type="button" @click="bulkMenuOpen = false; openAssign('transfer')">
                    <ArrowRightLeft />转移所有者
                  </button>
                  <button class="dropdown-item" type="button" @click="bulkMenuOpen = false; openAssign('unshare')">
                    <UserMinus />取消分配
                  </button>
                  <hr class="dropdown-divider" />
                  <button class="dropdown-item text-danger" type="button" @click="bulkMenuOpen = false; removeSelected()">
                    <Trash2 />删除所选 ({{ selectedIds.length }})
                  </button>
                  <button class="dropdown-item" type="button" @click="bulkMenuOpen = false; selectedIds = []">
                    <X />取消选择
                  </button>
                </div>
              </div>

              <button
                v-if="selectedIds.length"
                class="btn btn-outline-danger"
                type="button"
                :disabled="batchDeleting"
                @click="removeSelected"
              >
                <span v-if="batchDeleting" class="spinner-border spinner-border-sm"></span>
                <Trash2 v-else />删除 ({{ selectedIds.length }})
              </button>

              <button class="btn btn-outline-secondary" type="button" @click="trashDrawer = true">
                <Trash2 />回收站
                <span v-if="trash.total > 0" class="count-pill danger">{{ trash.total }}</span>
              </button>
            </template>

            <span v-if="!isAdmin" class="badge text-bg-primary">
              {{ module.access.scope === 'all' ? '全部记录' : '我的与共享记录' }}
            </span>

            <button v-if="keyword || activeFiltersCount > 0" class="btn btn-ghost" type="button" @click="clearSearch">
              <FunnelX />清空条件
            </button>
          </div>

          <div class="toolbar-group">
            <div class="search-box" style="width: 260px">
              <Search />
              <input
                v-model="keyword"
                class="form-control"
                placeholder="搜索记录，回车确认…"
                @keyup.enter="applySearch"
              />
              <button
                v-if="keyword"
                class="search-box-clear"
                type="button"
                aria-label="清除关键词"
                @click="keyword = ''; applySearch()"
              >
                <X />
              </button>
            </div>

            <div v-if="hasImageFields" class="image-toggle form-check form-switch mb-0">
              <input
                id="imgAuto"
                v-model="imageAutoLoad"
                class="form-check-input"
                type="checkbox"
                role="switch"
                @change="onImageToggle"
              />
              <label for="imgAuto" class="form-check-label">
                {{ imageAutoLoad ? '图片自动加载' : '图片手动点击' }}
              </label>
            </div>

            <button
              class="btn"
              :class="filtersVisible || activeFiltersCount > 0 ? 'btn-outline-primary' : 'btn-outline-secondary'"
              type="button"
              @click="filtersVisible = !filtersVisible"
            >
              <SlidersHorizontal />筛选
              <span v-if="activeFiltersCount > 0" class="count-pill accent">{{ activeFiltersCount }}</span>
            </button>

            <button class="btn btn-outline-secondary px-2" type="button" v-tip="'刷新数据'" @click="reload()">
              <RotateCw />
            </button>
          </div>
        </div>

        <!-- OVH 无外框数据表格（独立圆角浅冰蓝表头条 + 纯白无界行） -->
        <div class="ovh-table-wrap">

        <!-- 高级筛选面板 -->
        <div v-if="filtersVisible" class="filter-panel">
          <div v-if="!searchableFields.length" class="callout">
            <Info />
            <span>当前板块没有开启「支持搜索与筛选」的字段，可前往「字段管理」中开启。</span>
          </div>
          <template v-else>
            <div class="filter-head">
              <span class="section-label mb-0">
                <SlidersHorizontal />筛选条件
                <span class="section-label-hint">所有条件同时满足（且）</span>
              </span>
            </div>
            <div class="filter-rows">
              <div v-for="(filter, index) in filters" :key="index" class="filter-row">
                <span class="filter-idx">{{ index === 0 ? '当' : '且' }}</span>
                <select v-model="filter.field" class="form-select form-select-sm filter-field-select">
                  <option v-for="mf in searchableFields" :key="mf.field.code" :value="mf.field.code">
                    {{ mf.field.name }} ({{ mf.field.code }})
                  </option>
                </select>
                <select v-model="filter.op" class="form-select form-select-sm filter-op-select">
                  <option v-for="op in filterOps" :key="op.value" :value="op.value">{{ op.label }}</option>
                </select>
                <input
                  v-model="filter.value"
                  class="form-control form-control-sm flex-grow-1"
                  placeholder="输入过滤值…"
                  :disabled="filter.op === 'empty' || filter.op === 'not_empty'"
                  @keyup.enter="applySearch"
                />
                <button class="icon-button sm danger" type="button" v-tip="'移除此条件'" @click="filters.splice(index, 1)">
                  <X />
                </button>
              </div>
              <div v-if="!filters.length" class="filter-empty">尚未添加条件，点击下方「添加条件」开始。</div>
            </div>

            <div class="filter-actions">
              <button class="btn btn-sm btn-ghost" type="button" @click="addFilter">
                <Plus />添加条件
              </button>
              <div class="d-flex gap-2">
                <button class="btn btn-sm btn-outline-secondary" type="button" @click="filtersVisible = false">收起</button>
                <button class="btn btn-sm btn-primary" type="button" @click="applySearch">应用筛选</button>
              </div>
            </div>
          </template>
        </div>

        <!-- 数据表格 -->
        <SkeletonTable v-if="loading && firstLoad" :rows="10" :cols="6" />
        <div v-else class="table-responsive">
          <table class="table table-hover align-middle records-table" :class="{ 'is-drag-selecting': dragSel.dragging }">
            <thead>
              <tr>
                <th v-if="isAdmin" style="width: 44px" class="col-check">
                  <input
                    type="checkbox"
                    class="form-check-input"
                    :checked="allPageSelected"
                    :indeterminate.prop="somePageSelected"
                    @change="togglePage"
                  />
                </th>
                <th style="width: 56px" class="text-center">#</th>
                <th
                  v-for="col in listColumns"
                  :key="col.key || col.field_id"
                  :style="thStyle(col)"
                  class="resizable-th"
                >
                  <div class="d-flex align-items-center gap-1">
                    <span class="text-truncate">{{ col.field.name }}</span>
                    <span v-if="col.is_calculated" class="badge text-bg-info calc-badge">计算</span>
                  </div>
                  <span v-if="!col.is_calculated" class="col-resizer" @mousedown="startResize($event, col)"></span>
                </th>
                <th v-if="isAdmin" style="width: 130px">所有者</th>
                <th style="width: 148px">更新时间</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, i) in data.items"
                :key="row.id"
                :class="{ 'is-selected': selectedIds.includes(row.id) }"
                @mousedown="onRowMousedown($event, i)"
                @mouseenter="onRowMouseenter(i)"
                @dblclick="onRowDblClick($event, row)"
                @contextmenu.prevent="openCtxMenu($event, row)"
              >
                <td v-if="isAdmin" class="col-check">
                  <input v-model="selectedIds" type="checkbox" class="form-check-input" :value="row.id" />
                </td>
                <td class="cell-mono cell-faint text-center">{{ (page - 1) * pageSize + i + 1 }}</td>
                <td
                  v-for="col in listColumns"
                  :key="col.key || col.field_id"
                  class="cell-clip"
                  :title="cellTitle(col, row)"
                >
                  <CellDisplay
                    :field="col.field"
                    :value="row.data[col.field.code]"
                    :meta="row.data._calculated_meta?.[col.field.code]"
                    :auto-load-image="imageAutoLoad"
                  />
                </td>
                <td v-if="isAdmin" class="cell-clip">
                  <span class="owner-cell">
                    <span v-if="row.owner" class="owner-name">{{ row.owner }}</span>
                    <span v-else class="cell-faint">无主</span>
                    <span v-if="row.shared_count" class="badge text-bg-info" v-tip="`已分配给 ${row.shared_count} 人`">
                      <Users />{{ row.shared_count }}
                    </span>
                  </span>
                </td>
                <td class="cell-mono cell-muted cell-last">
                  <span>{{ formatTime(row.updated_at) }}</span>
                  <div class="row-float-actions" @dblclick.stop>
                    <button
                      v-if="module?.access.can_create"
                      class="icon-button sm primary"
                      v-tip="'复制为新记录'"
                      @click="duplicateRecord(row)"
                    >
                      <Copy />
                    </button>
                    <button class="icon-button sm" v-tip="'复制文本'" @click="copyRecord(row)"><Clipboard /></button>
                    <button v-if="isAdmin" class="icon-button sm primary" v-tip="'分配给用户'" @click="openAccess(row)"><UserPlus /></button>
                    <button v-if="row.can_edit" class="icon-button sm primary" v-tip="'编辑 (或双击行)'" @click="openEdit(row)"><Pencil /></button>
                    <button v-else class="icon-button sm" v-tip="'只读 · 查看详情'" @click="openEdit(row, true)"><Eye /></button>
                    <button v-if="row.can_delete" class="icon-button sm danger" v-tip="'移入回收站'" @click="remove(row)"><Trash2 /></button>
                  </div>
                </td>
              </tr>
            </tbody>
            <!-- 求和汇总栏 -->
            <tfoot v-if="hasSummaryFields && data.items.length">
              <tr class="summary-row">
                <td v-if="isAdmin"></td>
                <td class="text-center">合计</td>
                <td v-for="col in listColumns" :key="col.key || col.field_id">
                  <span
                    v-if="isSummaryCol(col)"
                    class="summary-value"
                    :title="`当前页小计：${formatNumber(pageSum(col.field.code))}\n当前筛选总计：${formatNumber(stats.sums[col.field.code] || 0)}`"
                  >
                    {{ formatNumber(pageSum(col.field.code)) }}
                  </span>
                </td>
                <td v-if="isAdmin"></td>
                <td></td>
              </tr>
            </tfoot>
          </table>

          <div v-if="!data.items.length" class="empty-state">
            <Inbox />
            <template v-if="keyword || activeFiltersCount > 0">
              <div class="empty-state-title">没有符合条件的记录</div>
              <p>尝试调整关键词或筛选条件。</p>
              <button class="btn btn-outline-secondary btn-sm" @click="clearSearch"><FunnelX />清空条件</button>
            </template>
            <template v-else-if="module.access.can_create">
              <div class="empty-state-title">暂无数据记录</div>
              <p>点击「新增记录」开始录入第一条数据。</p>
              <button class="btn btn-primary btn-sm" @click="openEdit()"><Plus />新增第一条记录</button>
            </template>
            <template v-else>
              <div class="empty-state-title">暂无可查看的记录</div>
              <p>管理员分配给你的记录会显示在这里。</p>
            </template>
          </div>
        </div>

        </div>

        <!-- OVH 居中分页（位于白底表格卡片下方） -->
        <div class="mt-3">
          <BasePagination
            :total="data.total"
            :page="page"
            :page-size="pageSize"
            :page-sizes="[20, 50, 100, 200]"
            @update:page="onPage"
            @update:page-size="onPageSize"
          />
        </div>

        <!-- 鼠标右键上下文快捷菜单 -->
        <div
          v-if="ctxMenu.visible && ctxMenu.row"
          class="ovh-ctx-menu"
          :style="{ top: `${ctxMenu.y}px`, left: `${ctxMenu.x}px` }"
          @mousedown.stop
        >
          <div class="ovh-ctx-head">记录 #{{ ctxMenu.row.id }}</div>
          <button
            v-if="ctxMenu.row.can_edit"
            type="button"
            class="ovh-ctx-item"
            @click="onCtxAct(() => openEdit(ctxMenu.row!))"
          >
            <Pencil />编辑记录
          </button>
          <button
            v-else
            type="button"
            class="ovh-ctx-item"
            @click="onCtxAct(() => openEdit(ctxMenu.row!, true))"
          >
            <Eye />查看详情
          </button>
          <button
            v-if="module?.access.can_create"
            type="button"
            class="ovh-ctx-item"
            @click="onCtxAct(() => duplicateRecord(ctxMenu.row!))"
          >
            <Copy />复制为新记录
          </button>
          <button
            type="button"
            class="ovh-ctx-item"
            @click="onCtxAct(() => copyRecord(ctxMenu.row!))"
          >
            <Clipboard />复制记录文本
          </button>
          <button
            v-if="isAdmin"
            type="button"
            class="ovh-ctx-item"
            @click="onCtxAct(() => openAccess(ctxMenu.row!))"
          >
            <UserPlus />分配访问权限
          </button>
          <template v-if="ctxMenu.row.can_delete">
            <div class="ovh-ctx-sep"></div>
            <button
              type="button"
              class="ovh-ctx-item is-danger"
              @click="onCtxAct(() => remove(ctxMenu.row!))"
            >
              <Trash2 />移入回收站
            </button>
          </template>
        </div>
      </template>
    </template>

    <!-- 编辑 / 新增记录抽屉 -->
    <BaseModal
      v-model="editDrawer"
      :title="editing.readonly ? `查看记录 #${editing.id}` : editing.id ? `编辑记录 #${editing.id}` : editing.copyFromId ? `复制新增记录（基于 #${editing.copyFromId}）` : '新增记录'"
      drawer
      width="560px"
      :close-on-backdrop="false"
    >
      <div v-if="editing.readonly" class="callout mb-3">
        <Lock />
        <span>这条记录是分配给你的只读记录，如需修改请联系管理员。</span>
      </div>
      <DynamicForm v-if="module" :module="module" v-model="editing.data" :loading="saving || editing.readonly" />
      <template #footer>
        <button class="btn btn-outline-secondary" @click="editDrawer = false">{{ editing.readonly ? '关闭' : '取消' }}</button>
        <button v-if="!editing.readonly" class="btn btn-primary" :disabled="saving" @click="save">
          <span v-if="saving" class="spinner-border spinner-border-sm"></span>保存记录
        </button>
      </template>
    </BaseModal>

    <!-- 批量分配 / 转移 / 取消分配 -->
    <BaseModal v-model="assignDialog" :title="assignTitle" :close-on-backdrop="false">
      <div class="callout mb-3" :class="{ warning: assign.mode === 'transfer' }">
        <component :is="assign.mode === 'transfer' ? TriangleAlert : Info" />
        <span v-if="assign.mode === 'share'">被分配的用户可以在侧边栏看到这个板块，并查看选中的 {{ selectedIds.length }} 条记录。</span>
        <span v-else-if="assign.mode === 'transfer'">选中的 {{ selectedIds.length }} 条记录将归新所有者所有，原所有者将不再能看到它们（除非另行分配）。</span>
        <span v-else>从选中用户的可见范围中移除这 {{ selectedIds.length }} 条记录（不影响记录本身）。</span>
      </div>

      <div v-if="assign.mode === 'share'" class="mb-3">
        <label class="form-label">权限</label>
        <div class="segmented">
          <button type="button" class="segmented-btn" :class="{ active: !assign.can_edit }" @click="assign.can_edit = false"><Eye />只读</button>
          <button type="button" class="segmented-btn" :class="{ active: assign.can_edit }" @click="assign.can_edit = true"><Pencil />可编辑</button>
        </div>
      </div>

      <label class="form-label">{{ assign.mode === 'transfer' ? '新所有者' : '选择用户' }}</label>
      <div class="search-box mb-2" style="width: 100%">
        <Search />
        <input v-model="assign.keyword" class="form-control form-control-sm" placeholder="搜索用户" />
      </div>
      <div class="user-pick">
        <label v-for="u in pickableUsers" :key="u.id" class="user-pick-row" :class="{ on: assign.userIds.includes(u.id) }">
          <input
            :type="assign.mode === 'transfer' ? 'radio' : 'checkbox'"
            class="form-check-input"
            name="assign-user"
            :checked="assign.userIds.includes(u.id)"
            @change="pickUser(u.id)"
          />
          <span class="user-pick-avatar" :class="{ admin: u.role === 'admin' }">{{ (u.display_name || u.username).slice(0, 1).toUpperCase() }}</span>
          <span class="name-text">
            <span class="name-title">{{ u.display_name || u.username }}</span>
            <span class="name-sub">@{{ u.username }}{{ u.role === 'admin' ? ' · 管理员' : '' }}</span>
          </span>
        </label>
        <div v-if="!pickableUsers.length" class="user-pick-empty">
          {{ users.length ? '没有匹配的用户' : '还没有其他用户，可先在「用户管理」中创建或开放注册' }}
        </div>
      </div>
      <template #footer>
        <button class="btn btn-outline-secondary" @click="assignDialog = false">取消</button>
        <button
          class="btn"
          :class="assign.mode === 'unshare' ? 'btn-danger' : 'btn-primary'"
          :disabled="assigning || !assign.userIds.length"
          @click="submitAssign"
        >
          <span v-if="assigning" class="spinner-border spinner-border-sm"></span>
          {{ assign.mode === 'share' ? '确认分配' : assign.mode === 'transfer' ? '确认转移' : '取消分配' }}
        </button>
      </template>
    </BaseModal>

    <!-- 单条记录的分配名单 -->
    <BaseModal v-model="accessDialog" :title="`记录 #${accessRecordId} · 访问权限`" :close-on-backdrop="false">
      <div class="access-owner">
        <span class="access-label">所有者</span>
        <span class="access-owner-name">{{ access.owner || '无主（仅管理员可见）' }}</span>
        <span class="cell-faint">· 可查看、编辑、删除</span>
      </div>

      <label class="form-label mt-3">已分配给</label>
      <div class="access-list">
        <div v-for="(item, idx) in access.shared" :key="item.user_id" class="access-row">
          <span class="user-pick-avatar">{{ (item.display_name || item.username).slice(0, 1).toUpperCase() }}</span>
          <span class="name-text flex-grow-1">
            <span class="name-title">{{ item.display_name || item.username }}</span>
            <span class="name-sub">@{{ item.username }}</span>
          </span>
          <div class="segmented">
            <button type="button" class="segmented-btn" :class="{ active: !item.can_edit }" @click="item.can_edit = false">只读</button>
            <button type="button" class="segmented-btn" :class="{ active: item.can_edit }" @click="item.can_edit = true">可编辑</button>
          </div>
          <button class="icon-button sm danger" type="button" v-tip="'移除'" @click="access.shared.splice(idx, 1)"><X /></button>
        </div>
        <div v-if="!access.shared.length" class="user-pick-empty">尚未分配给任何人</div>
      </div>

      <div class="access-add">
        <select v-model="accessAddId" class="form-select form-select-sm">
          <option :value="null">添加用户…</option>
          <option v-for="u in accessCandidates" :key="u.id" :value="u.id">
            {{ u.display_name ? `${u.display_name} (@${u.username})` : u.username }}
          </option>
        </select>
        <button class="btn btn-sm btn-outline-secondary" type="button" :disabled="!accessAddId" @click="addAccessUser"><Plus />添加</button>
      </div>

      <template #footer>
        <button class="btn btn-outline-secondary" @click="accessDialog = false">取消</button>
        <button class="btn btn-primary" :disabled="savingAccess" @click="saveAccess">
          <span v-if="savingAccess" class="spinner-border spinner-border-sm"></span>保存
        </button>
      </template>
    </BaseModal>

    <!-- 回收站抽屉 -->
    <BaseModal v-model="trashDrawer" title="回收站" drawer width="820px">
      <div class="trash-bar">
        <span class="toolbar-meta">
          已选 <strong>{{ selectedTrashIds.length }}</strong> / 共 <strong>{{ trash.total }}</strong> 条
        </span>
        <div class="d-flex gap-2">
          <button class="btn btn-sm btn-outline-danger" :disabled="!selectedTrashIds.length" @click="purgeSelectedTrash">
            <Trash2 />彻底删除所选
          </button>
          <button class="btn btn-sm btn-danger" :disabled="!trash.items.length" @click="purgeAllTrash">
            清空回收站
          </button>
        </div>
      </div>
      <div class="callout mb-3">
        <Info />
        <span>回收站中的记录可随时恢复；彻底删除后将无法找回。</span>
      </div>
      <div class="trash-table">
        <div class="table-responsive">
          <table class="table table-hover table-sm align-middle">
            <thead>
              <tr>
                <th style="width: 40px">
                  <input type="checkbox" class="form-check-input" :checked="allTrashSelected" @change="toggleAllTrash" />
                </th>
                <th style="width: 44px">#</th>
                <th v-for="mf in listColumns.slice(0, 3)" :key="mf.field_id">{{ mf.field.name }}</th>
                <th style="width: 156px">删除时间</th>
                <th style="width: 84px" class="text-end">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in trash.items" :key="row.id">
                <td><input v-model="selectedTrashIds" type="checkbox" class="form-check-input" :value="row.id" /></td>
                <td class="cell-mono cell-faint">{{ i + 1 }}</td>
                <td v-for="mf in listColumns.slice(0, 3)" :key="mf.field_id" class="cell-clip" style="max-width: 200px">
                  <CellDisplay
                    :field="mf.field"
                    :value="row.data[mf.field.code]"
                    :meta="row.data._calculated_meta?.[mf.field.code]"
                    :auto-load-image="imageAutoLoad"
                  />
                </td>
                <td class="cell-mono cell-muted">{{ formatTime(row.updated_at) }}</td>
                <td class="text-end">
                  <div class="row-actions">
                    <button class="icon-button sm primary" v-tip="'恢复记录'" @click="restore(row)"><ArchiveRestore /></button>
                    <button class="icon-button sm danger" v-tip="'彻底删除'" @click="purge(row)"><Trash2 /></button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="!trash.items.length" class="empty-state">
            <Trash2 />
            <span>回收站当前为空</span>
          </div>
        </div>
      </div>
    </BaseModal>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import {
  ArchiveRestore,
  ArrowRightLeft,
  Clipboard,
  Copy,
  Eye,
  FunnelX,
  Inbox,
  Info,
  ListTree,
  Lock,
  Pencil,
  Plus,
  RotateCw,
  Search,
  Settings2,
  SlidersHorizontal,
  Trash2,
  TriangleAlert,
  UserMinus,
  UserPlus,
  Users,
  X,
} from 'lucide-vue-next'
import DynamicForm from '@/components/DynamicForm.vue'
import CellDisplay from '@/components/CellDisplay.vue'
import { moduleApi, recordApi, userApi, type ModuleOut, type RecordAccess, type RecordOut, type UserOut } from '@/api'
import { useNavStore } from '@/stores/nav'
import { useAuthStore } from '@/stores/auth'
import { toast, confirm } from '@/utils/ui'
import { vLoading } from '@/components/ui/loading'
import { vTip } from '@/components/ui/tooltip'
import BaseModal from '@/components/ui/BaseModal.vue'
import BasePagination from '@/components/ui/BasePagination.vue'
import SkeletonTable from '@/components/ui/SkeletonTable.vue'
import AppIcon from '@/components/AppIcon.vue'
import PageHeader from '@/components/ui/PageHeader.vue'

const route = useRoute()
const bulkMenuOpen = ref(false)
const batchDeleting = ref(false)
const ctxMenu = reactive<{ visible: boolean; x: number; y: number; row: RecordOut | null }>({
  visible: false,
  x: 0,
  y: 0,
  row: null,
})

function openCtxMenu(e: MouseEvent, row: RecordOut) {
  const menuW = 176
  const menuH = 170
  ctxMenu.row = row
  ctxMenu.x = Math.min(e.clientX, window.innerWidth - menuW - 8)
  ctxMenu.y = Math.min(e.clientY, window.innerHeight - menuH - 8)
  ctxMenu.visible = true
}

function closeCtxMenu() {
  if (ctxMenu.visible) ctxMenu.visible = false
}

function onCtxAct(fn: () => void) {
  ctxMenu.visible = false
  fn()
}

function onRowDblClick(e: MouseEvent, row: RecordOut) {
  const target = e.target as HTMLElement
  if (target.closest('input, button, a, .row-float-actions, .cell-img-box, .secret-cell')) return
  openEdit(row, !row.can_edit)
}
const nav = useNavStore()
const auth = useAuthStore()
const isAdmin = computed(() => auth.isAdmin)
const moduleId = computed(() => {
  const id = Number(route.params.moduleId)
  return Number.isInteger(id) && id > 0 ? id : null
})

const module = ref<ModuleOut | null>(null)
const loading = ref(false)
const firstLoad = ref(true)
const saving = ref(false)

const data = reactive<{ items: RecordOut[]; total: number }>({ items: [], total: 0 })
const stats = reactive<{ sums: Record<string, number> }>({ sums: {} })
const trash = reactive<{ items: RecordOut[]; total: number }>({ items: [], total: 0 })
const page = ref(1)
const pageSize = ref(50)
const keyword = ref('')
const filtersVisible = ref(false)
const imageAutoLoad = ref(true)
const filters = ref<{ field: string; op: string; value: any }[]>([])
const colWidths = reactive<Record<string, number>>({})

const editDrawer = ref(false)
const trashDrawer = ref(false)
const selectedTrashIds = ref<number[]>([])
const editing = reactive<{ id: number | null; copyFromId: number | null; data: Record<string, any>; readonly: boolean }>({
  id: null,
  copyFromId: null,
  data: {},
  readonly: false,
})
let loadToken = 0
let activeController: AbortController | null = null

const activeFiltersCount = computed(() => filters.value.filter((f) => f.field && f.op && f.value !== '').length)

const categoryName = computed(() => {
  const id = module.value?.category_id
  return (id && nav.categories.find((c) => c.id === id)?.name) || '数据板块'
})

function isAbortError(err: unknown): boolean {
  if (!err || typeof err !== 'object') return false
  const e = err as any
  return e.code === 'ERR_CANCELED' || e.name === 'CanceledError' || e.name === 'AbortError'
}

function newLoadCtx() {
  if (activeController) activeController.abort()
  const controller = new AbortController()
  activeController = controller
  const token = ++loadToken
  return { token, signal: controller.signal }
}

const listColumns = computed<any[]>(() =>
  module.value
    ? [
        ...module.value.fields.filter((mf) => mf.show_in_list).map((mf) => ({
          ...mf,
          sort_order: Number(mf.sort_order || 0) + 1,
          is_calculated: false,
        })),
        ...(module.value.calculated_fields || [])
          .filter((cf) => cf.show_in_list)
          .map((cf) => ({
            key: `calc:${cf.code}`,
            field_id: `calc:${cf.code}`,
            column_width: 130,
            sort_order: cf.sort_order ?? 9999,
            is_calculated: true,
            show_in_list: true,
            field: {
              id: 0,
              code: cf.code,
              name: cf.name,
              type: 'number',
              options: { precision: cf.precision },
              is_encrypted: false,
              is_searchable: false,
              enable_summary: cf.enable_summary,
              description: null,
              created_at: '',
            },
          })),
      ].sort((a, b) => {
        const diff = Number(a.sort_order || 0) - Number(b.sort_order || 0)
        if (diff !== 0) return diff
        return Number(a.is_calculated || false) - Number(b.is_calculated || false)
      })
    : []
)

const hasImageFields = computed(() => listColumns.value.some((mf) => mf.field.type === 'image'))

const summaryFields = computed(() =>
  listColumns.value.filter((mf) => mf.field.type === 'number' && mf.field.enable_summary)
)
const hasSummaryFields = computed(() => summaryFields.value.length > 0)
function isSummaryCol(col: any) {
  return summaryFields.value.some((mf) => mf.field.code === col.field.code)
}

const searchableFields = computed(() =>
  module.value
    ? module.value.fields.filter((mf) => {
        const f = mf.field
        return f.is_searchable && !f.is_encrypted && !['password', 'image', 'file', 'json'].includes(f.type)
      })
    : []
)

const filterOps = [
  { label: '包含', value: 'contains' },
  { label: '不包含', value: 'not_contains' },
  { label: '等于', value: 'eq' },
  { label: '不等于', value: 'neq' },
  { label: '大于', value: 'gt' },
  { label: '大于等于', value: 'gte' },
  { label: '小于', value: 'lt' },
  { label: '小于等于', value: 'lte' },
  { label: '为空', value: 'empty' },
  { label: '不为空', value: 'not_empty' },
]

/* ---------- 列宽 ---------- */
function thStyle(col: any) {
  const w = colWidths[col.field.code] ?? col.column_width ?? 160
  return { width: `${w}px`, minWidth: `${w}px` }
}

function startResize(e: MouseEvent, col: any) {
  e.preventDefault()
  e.stopPropagation()
  const code = col.field.code
  const th = (e.target as HTMLElement).closest('th') as HTMLElement
  const startX = e.clientX
  const startW = th ? th.offsetWidth : colWidths[code] ?? col.column_width ?? 160
  const move = (ev: MouseEvent) => {
    colWidths[code] = Math.max(60, Math.round(startW + (ev.clientX - startX)))
  }
  const up = () => {
    document.removeEventListener('mousemove', move)
    document.removeEventListener('mouseup', up)
    if (!col.is_calculated) persistWidth(code, colWidths[code])
  }
  document.addEventListener('mousemove', move)
  document.addEventListener('mouseup', up)
}

async function persistWidth(code: string, width: number) {
  if (!module.value || !width || !isAdmin.value) return
  const mf = module.value.fields.find((x) => x.field.code === code)
  if (!mf || width === mf.column_width) return
  mf.column_width = width
  try {
    await moduleApi.updateField(module.value.id, mf.field_id, { column_width: width })
  } catch {
    // 静默失败
  }
}

function cellTitle(col: any, row: RecordOut) {
  if (col.field.type === 'image') return ''
  return valueToText(row.data[col.field.code])
}

function resetPageData() {
  selectedIds.value = []
  module.value = null
  data.items = []
  data.total = 0
  stats.sums = {}
  trash.items = []
  trash.total = 0
  selectedTrashIds.value = []
}

async function loadModule(id = moduleId.value) {
  if (!id) {
    if (activeController) {
      activeController.abort()
      activeController = null
    }
    loadToken += 1
    resetPageData()
    return
  }
  const { token, signal } = newLoadCtx()
  loading.value = true
  try {
    const { data: m } = await moduleApi.get(id, signal)
    if (token !== loadToken || moduleId.value !== id) return
    module.value = m
    imageAutoLoad.value = m.auto_load_images
    page.value = 1
    keyword.value = ''
    filters.value = []
    Object.keys(colWidths).forEach((k) => delete colWidths[k])
    await reload(id, { token, signal })
  } catch (err) {
    if (isAbortError(err)) return
    throw err
  } finally {
    if (token === loadToken) {
      loading.value = false
      firstLoad.value = false
    }
  }
}

async function reload(id = moduleId.value, ctx?: { token: number; signal: AbortSignal }) {
  if (!module.value || !id) return
  const { token, signal } = ctx ?? newLoadCtx()
  const activeFilters = filters.value.filter((f) => f.field && f.op)
  const hasSearch = !!keyword.value.trim() || activeFilters.length > 0
  const searchPayload = {
    keyword: keyword.value.trim() || undefined,
    filters: activeFilters,
    page: page.value,
    page_size: pageSize.value,
  }
  try {
    const { data: d } = hasSearch
      ? await recordApi.search(id, searchPayload, signal)
      : await recordApi.list(id, { page: page.value, page_size: pageSize.value }, signal)
    if (token !== loadToken || moduleId.value !== id) return
    data.items = d.items
    data.total = d.total
    selectedIds.value = selectedIds.value.filter((rid) => d.items.some((r) => r.id === rid))
    if (hasSummaryFields.value) {
      const { data: s } = await recordApi.stats(id, searchPayload, signal)
      if (token !== loadToken || moduleId.value !== id) return
      stats.sums = s.sums
    } else {
      stats.sums = {}
    }
  } catch (err) {
    if (isAbortError(err)) return
    throw err
  }
}

function onPage(p: number) {
  page.value = p
  reload()
}
function onPageSize(s: number) {
  pageSize.value = s
  page.value = 1
  reload()
}

function pageSum(code: string) {
  return data.items.reduce((sum, row) => {
    const value = row.data[code]
    if (value === null || value === undefined || value === '') return sum
    const num = Number(value)
    return Number.isFinite(num) ? sum + num : sum
  }, 0)
}

function formatNumber(value: number) {
  return Number(value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function onImageToggle() {
  // 成员没有修改板块配置的权限，只在本次浏览中生效
  if (isAdmin.value) saveImageAutoLoad()
}

async function saveImageAutoLoad() {
  if (!module.value) return
  await moduleApi.update(module.value.id, { auto_load_images: imageAutoLoad.value })
  module.value.auto_load_images = imageAutoLoad.value
  toast(imageAutoLoad.value ? '已开启图片自动加载' : '已关闭图片自动加载', 'success')
}

function addFilter() {
  const first = searchableFields.value[0]
  filters.value.push({ field: first?.field.code || '', op: 'contains', value: '' })
}

function applySearch() {
  page.value = 1
  reload()
}

function clearSearch() {
  keyword.value = ''
  filters.value = []
  page.value = 1
  reload()
}

async function loadTrash() {
  const id = moduleId.value
  if (!id) return
  const { data: d } = await recordApi.trash(id, { page: 1, page_size: 100 })
  if (moduleId.value !== id) return
  trash.items = d.items
  trash.total = d.total
  selectedTrashIds.value = []
}

const allTrashSelected = computed(() => trash.items.length > 0 && selectedTrashIds.value.length === trash.items.length)
function toggleAllTrash(e: Event) {
  selectedTrashIds.value = (e.target as HTMLInputElement).checked ? trash.items.map((r) => r.id) : []
}

async function openEdit(row?: RecordOut, readonly = false) {
  const id = moduleId.value
  if (!id) return
  editing.id = row?.id || null
  editing.copyFromId = null
  editing.readonly = readonly
  if (row) {
    const { data: full } = await recordApi.get(id, row.id)
    if (moduleId.value !== id) return
    editing.data = { ...full.data }
  } else {
    editing.data = {}
  }
  editDrawer.value = true
}

async function duplicateRecord(row: RecordOut) {
  const id = moduleId.value
  if (!id || !module.value?.access.can_create) return
  const { data: full } = await recordApi.get(id, row.id)
  if (moduleId.value !== id) return
  const allowedCodes = new Set((module.value?.fields || []).map((mf) => mf.field.code))
  const cloned: Record<string, any> = {}
  for (const [k, v] of Object.entries(full.data || {})) {
    if (allowedCodes.has(k)) {
      cloned[k] = Array.isArray(v) ? [...v] : v && typeof v === 'object' ? JSON.parse(JSON.stringify(v)) : v
    }
  }
  editing.id = null
  editing.copyFromId = row.id
  editing.readonly = false
  editing.data = cloned
  editDrawer.value = true
}

async function save() {
  const id = moduleId.value
  if (!id) return
  saving.value = true
  try {
    if (editing.id) {
      await recordApi.update(id, editing.id, editing.data)
    } else {
      await recordApi.create(id, editing.data)
    }
    if (moduleId.value !== id) return
    toast('已保存记录', 'success')
    editDrawer.value = false
    await reload(id)
  } finally {
    saving.value = false
  }
}

async function remove(row: RecordOut) {
  const id = moduleId.value
  if (!id) return
  if (!(await confirm('移入回收站？', { danger: true }))) return
  await recordApi.remove(id, row.id)
  if (moduleId.value !== id) return
  toast('已移入回收站', 'success')
  await reload(id)
}

async function removeSelected() {
  const id = moduleId.value
  const ids = [...selectedIds.value]
  if (!id || !ids.length) return
  if (
    !(await confirm(`确定将选中的 ${ids.length} 条记录移入回收站？`, {
      title: '批量移入回收站',
      confirmText: '确认删除',
      danger: true,
    }))
  ) {
    return
  }
  batchDeleting.value = true
  try {
    await Promise.all(ids.map((rid) => recordApi.remove(id, rid)))
    if (moduleId.value !== id) return
    selectedIds.value = []
    toast(`已将 ${ids.length} 条记录移入回收站`, 'success')
    await reload(id)
  } finally {
    batchDeleting.value = false
  }
}

async function restore(row: RecordOut) {
  const id = moduleId.value
  if (!id) return
  await recordApi.restore(id, row.id)
  if (moduleId.value !== id) return
  toast('已恢复记录', 'success')
  await loadTrash()
  await reload(id)
}

async function purge(row: RecordOut) {
  const id = moduleId.value
  if (!id) return
  if (!(await confirm('彻底删除？不可恢复', { danger: true }))) return
  await recordApi.purge(id, row.id)
  if (moduleId.value !== id) return
  toast('已彻底删除', 'success')
  await loadTrash()
}

async function purgeSelectedTrash() {
  const id = moduleId.value
  if (!id) return
  const ids = [...selectedTrashIds.value]
  if (!ids.length) return
  if (!(await confirm(`确定彻底删除选中 ${ids.length} 条记录？`, { title: '批量彻底删除', confirmText: '确认删除', danger: true }))) return
  const { data: result } = await recordApi.purgeTrash(id, ids)
  if (moduleId.value !== id) return
  toast(`已彻底删除 ${result.deleted} 条`, 'success')
  await loadTrash()
}

async function purgeAllTrash() {
  const id = moduleId.value
  if (!id) return
  if (!trash.items.length) return
  if (!(await confirm(`确定彻底删除回收站全部 ${trash.total} 条？`, { title: '一键彻底删除', confirmText: '确认删除', danger: true }))) return
  const { data: result } = await recordApi.purgeAllTrash(id)
  if (moduleId.value !== id) return
  toast(`已彻底删除 ${result.deleted} 条`, 'success')
  await loadTrash()
}

function valueToText(value: any) {
  if (value === null || value === undefined || value === '') return ''
  if (Array.isArray(value)) return value.join(', ')
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

async function copyText(text: string) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text)
    return
  }
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.style.position = 'fixed'
  textarea.style.left = '-9999px'
  document.body.appendChild(textarea)
  textarea.focus()
  textarea.select()
  document.execCommand('copy')
  document.body.removeChild(textarea)
}

async function copyRecord(row: RecordOut) {
  if (!module.value) return
  const lines = module.value.fields
    .map((mf) => {
      const text = valueToText(row.data[mf.field.code])
      return text ? `${mf.field.name}: ${text}` : ''
    })
    .filter(Boolean)
  if (!lines.length) {
    toast('没有可复制的文本', 'warning')
    return
  }
  await copyText(lines.join('\n'))
  toast('已复制记录文本', 'success')
}

function formatTime(s: string) {
  return s ? new Date(s).toLocaleString('zh-CN') : ''
}

/* ---------- 选择 / 左键拖动多选 / 分配（管理员） ---------- */
const selectedIds = ref<number[]>([])
const allPageSelected = computed(() => data.items.length > 0 && data.items.every((r) => selectedIds.value.includes(r.id)))
const somePageSelected = computed(() => !allPageSelected.value && data.items.some((r) => selectedIds.value.includes(r.id)))

function togglePage() {
  const ids = data.items.map((r) => r.id)
  selectedIds.value = allPageSelected.value
    ? selectedIds.value.filter((rid) => !ids.includes(rid))
    : Array.from(new Set([...selectedIds.value, ...ids]))
}

const lastAnchorIdx = ref<number | null>(null)
const dragSel = reactive({
  active: false,
  dragging: false,
  startIdx: -1,
  append: false,
  unselect: false,
  baseIds: [] as number[],
})

function applyDragRange(endIdx: number) {
  const lo = Math.min(dragSel.startIdx, endIdx)
  const hi = Math.max(dragSel.startIdx, endIdx)
  const rangeIds = data.items.slice(lo, hi + 1).map((r) => r.id)
  if (dragSel.unselect) {
    selectedIds.value = dragSel.baseIds.filter((id) => !rangeIds.includes(id))
  } else if (dragSel.append) {
    selectedIds.value = Array.from(new Set([...dragSel.baseIds, ...rangeIds]))
  } else {
    selectedIds.value = rangeIds
  }
}

function onRowMousedown(e: MouseEvent, idx: number) {
  if (!isAdmin.value || e.button !== 0) return
  const target = e.target as HTMLElement
  if (target.closest('button, a, .row-float-actions, .cell-img-box, .secret-cell')) return

  const row = data.items[idx]
  if (!row) return

  // Shift + 左键点击：直接连续范围选中
  if (e.shiftKey && lastAnchorIdx.value !== null) {
    e.preventDefault()
    window.getSelection()?.removeAllRanges()
    const lo = Math.min(lastAnchorIdx.value, idx)
    const hi = Math.max(lastAnchorIdx.value, idx)
    const rangeIds = data.items.slice(lo, hi + 1).map((r) => r.id)
    selectedIds.value = Array.from(new Set([...selectedIds.value, ...rangeIds]))
    return
  }

  lastAnchorIdx.value = idx
  const inCheckCol = !!target.closest('.col-check')
  const alreadySelected = selectedIds.value.includes(row.id)

  dragSel.active = true
  dragSel.dragging = false
  dragSel.startIdx = idx
  dragSel.baseIds = [...selectedIds.value]
  dragSel.append = e.ctrlKey || e.metaKey || inCheckCol
  dragSel.unselect = inCheckCol && alreadySelected
}

function onRowMouseenter(idx: number) {
  if (!dragSel.active) return
  if (!dragSel.dragging && idx !== dragSel.startIdx) {
    dragSel.dragging = true
  }
  if (dragSel.dragging) {
    window.getSelection()?.removeAllRanges()
    applyDragRange(idx)
  }
}

function endDragSelect() {
  if (dragSel.active) {
    dragSel.active = false
    dragSel.dragging = false
  }
}

const users = ref<UserOut[]>([])
let usersLoaded = false
async function ensureUsers() {
  if (usersLoaded) return
  const { data: list } = await userApi.list()
  users.value = list.filter((u) => u.is_active)
  usersLoaded = true
}

type AssignMode = 'share' | 'unshare' | 'transfer'
const assignDialog = ref(false)
const assigning = ref(false)
const assign = reactive({ mode: 'share' as AssignMode, can_edit: false, userIds: [] as number[], keyword: '' })
const assignTitle = computed(
  () => ({ share: '分配给用户', transfer: '转移所有者', unshare: '取消分配' })[assign.mode]
)

const pickableUsers = computed(() => {
  const kw = assign.keyword.trim().toLowerCase()
  return users.value.filter((u) => {
    // 管理员本就能看到全部记录，分配 / 取消分配只针对成员；转移所有者可以选管理员
    if (assign.mode !== 'transfer' && u.role === 'admin') return false
    if (!kw) return true
    return u.username.toLowerCase().includes(kw) || (u.display_name || '').toLowerCase().includes(kw)
  })
})

async function openAssign(mode: AssignMode) {
  await ensureUsers()
  Object.assign(assign, { mode, can_edit: false, userIds: [], keyword: '' })
  assignDialog.value = true
}

function pickUser(uid: number) {
  if (assign.mode === 'transfer') {
    assign.userIds = [uid]
    return
  }
  const i = assign.userIds.indexOf(uid)
  if (i >= 0) assign.userIds.splice(i, 1)
  else assign.userIds.push(uid)
}

async function submitAssign() {
  const id = moduleId.value
  if (!id || !selectedIds.value.length || !assign.userIds.length) return
  assigning.value = true
  try {
    const { data: res } = await recordApi.assign(id, {
      record_ids: selectedIds.value,
      user_ids: assign.userIds,
      mode: assign.mode,
      can_edit: assign.can_edit,
    })
    const verb = { share: '已分配', transfer: '已转移', unshare: '已取消分配' }[assign.mode]
    toast(`${verb} ${res.records} 条记录`, 'success')
    assignDialog.value = false
    selectedIds.value = []
    await reload(id)
  } finally {
    assigning.value = false
  }
}

const accessDialog = ref(false)
const savingAccess = ref(false)
const accessRecordId = ref<number | null>(null)
const access = reactive<RecordAccess>({ owner_id: null, owner: null, shared: [] })
const accessAddId = ref<number | null>(null)
const accessCandidates = computed(() =>
  users.value.filter(
    (u) => u.role !== 'admin' && u.id !== access.owner_id && !access.shared.some((x) => x.user_id === u.id)
  )
)

async function openAccess(row: RecordOut) {
  const id = moduleId.value
  if (!id) return
  await ensureUsers()
  const { data: acc } = await recordApi.access(id, row.id)
  accessRecordId.value = row.id
  Object.assign(access, acc)
  accessAddId.value = null
  accessDialog.value = true
}

function addAccessUser() {
  const u = users.value.find((x) => x.id === accessAddId.value)
  if (!u) return
  access.shared.push({ user_id: u.id, username: u.username, display_name: u.display_name, can_edit: false })
  accessAddId.value = null
}

async function saveAccess() {
  const id = moduleId.value
  if (!id || !accessRecordId.value) return
  savingAccess.value = true
  try {
    await recordApi.setAccess(
      id,
      accessRecordId.value,
      access.shared.map((x) => ({ user_id: x.user_id, can_edit: x.can_edit }))
    )
    toast('访问权限已保存', 'success')
    accessDialog.value = false
    await reload(id)
  } finally {
    savingAccess.value = false
  }
}

watch(moduleId, loadModule, { immediate: true })
watch(trashDrawer, (v) => {
  if (v && isAdmin.value) loadTrash()
  else selectedTrashIds.value = []
})

onMounted(() => {
  window.addEventListener('mousedown', closeCtxMenu)
  window.addEventListener('mouseup', endDragSelect)
  window.addEventListener('scroll', closeCtxMenu, true)
})

onBeforeUnmount(() => {
  window.removeEventListener('mousedown', closeCtxMenu)
  window.removeEventListener('mouseup', endDragSelect)
  window.removeEventListener('scroll', closeCtxMenu, true)
  loadToken += 1
  if (activeController) {
    activeController.abort()
    activeController = null
  }
})
</script>

<style scoped>
.ovh-dd {
  position: relative;
}

.ovh-dd-menu {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 1040;
}

.mod-desc-tip {
  max-width: 360px;
  overflow: hidden;
  color: var(--text-faint);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.edge-foot {
  padding: 14px 24px;
}

/* ---------- 工具栏附件 ---------- */
.image-toggle {
  display: inline-flex;
  height: 33px;
  align-items: center;
  gap: 7px;
  padding: 0 11px;
  border: 1px solid var(--surface-border);
  border-radius: var(--radius);
  background: var(--bg-elev);
}

.image-toggle .form-check-input {
  float: none;
  margin: 0;
}

.image-toggle .form-check-label {
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

/* ---------- 高级筛选面板 ---------- */
.filter-panel {
  margin-bottom: 14px;
  padding: 16px 20px;
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-card);
  background: var(--bg-soft);
}

.filter-head {
  margin-bottom: 10px;
}

.filter-rows {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 8px;
  border: 1px solid var(--surface-border);
  border-radius: var(--radius);
  background: var(--bg-elev);
}

.filter-idx {
  display: inline-grid;
  width: 24px;
  height: 22px;
  flex-shrink: 0;
  place-items: center;
  border-radius: 5px;
  background: var(--bg-subtle);
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
}

.filter-field-select {
  max-width: 220px;
}

.filter-op-select {
  max-width: 130px;
}

.filter-empty {
  padding: 8px 0 4px 4px;
  color: var(--text-faint);
  font-size: 12px;
}

.filter-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--hairline);
}

/* ---------- 沉浸式 Edge-to-Edge 数据表 ---------- */
.records-table {
  width: 100%;
  table-layout: fixed;
}

.records-table.is-drag-selecting {
  user-select: none;
  cursor: pointer;
}

.records-table > tbody > tr > td {
  padding-top: 10px;
  padding-bottom: 10px;
}

.calc-badge {
  padding: 1px 5px;
  font-size: 10.5px;
}

.resizable-th {
  position: relative;
  user-select: none;
}

.col-resizer {
  position: absolute;
  top: 8px;
  right: 0;
  bottom: 8px;
  width: 4px;
  border-radius: 2px;
  background-color: transparent;
  cursor: col-resize;
  transition: background-color 0.14s ease;
}

.resizable-th:hover .col-resizer {
  background-color: var(--hairline-strong);
}

.col-resizer:hover {
  background-color: var(--accent) !important;
}

.records-table .col-sticky-end {
  position: sticky;
  right: 0;
  z-index: 2;
  background-color: var(--bg-elev) !important;
}

.records-table tbody > tr:hover > .col-sticky-end {
  background-color: var(--bg-hover) !important;
}

.records-table thead .col-sticky-end {
  background-color: var(--bg-table-head) !important;
}

.records-table .col-sticky-end::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 1px;
  background: var(--hairline);
}

.summary-row td {
  padding-top: 10px;
  padding-bottom: 10px;
  border-top: 1px solid var(--surface-border);
  background: var(--bg-soft) !important;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 600;
}

.summary-value {
  display: inline-block;
  padding: 2px 7px;
  border-radius: 5px;
  background: var(--bg-subtle);
  color: var(--text);
  cursor: help;
  font-family: var(--font-mono);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

/* ---------- 权限与悬浮批量操作岛 ---------- */
.scope-badge {
  align-self: center;
}

.records-table .col-check {
  padding-right: 0;
  text-align: center;
}

.records-table .col-check .form-check-input {
  margin: 0;
}

.records-table tr.is-selected > td {
  background: var(--accent-soft-subtle) !important;
}

.bulk-island {
  position: fixed;
  bottom: 24px;
  left: 50%;
  z-index: 1045;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 10px 7px 16px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 999px;
  background: #14161a;
  color: #f4f5f7;
  box-shadow: var(--shadow-xl);
  transform: translateX(-50%);
}

html[data-theme='dark'] .bulk-island {
  border-color: var(--surface-border);
  background: #f3f4f6;
  color: #111318;
}

.bulk-count {
  font-size: 13px;
  white-space: nowrap;
}

.bulk-count strong {
  font-variant-numeric: tabular-nums;
}

.bulk-sep {
  width: 1px;
  height: 16px;
  margin: 0 4px;
  background: rgba(255, 255, 255, 0.18);
}

html[data-theme='dark'] .bulk-sep {
  background: rgba(17, 19, 24, 0.18);
}

.bulk-btn {
  display: inline-flex;
  height: 28px;
  align-items: center;
  gap: 5px;
  padding: 0 10px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: inherit;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.12s ease;
}

.bulk-btn .lucide {
  width: 13.5px;
  height: 13.5px;
}

.bulk-btn:hover {
  background: rgba(255, 255, 255, 0.12);
}

html[data-theme='dark'] .bulk-btn:hover {
  background: rgba(17, 19, 24, 0.08);
}

.bulk-close {
  display: inline-grid;
  width: 26px;
  height: 26px;
  place-items: center;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: inherit;
  opacity: 0.7;
  cursor: pointer;
}

.bulk-close:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.12);
}

.bulk-close .lucide {
  width: 14px;
  height: 14px;
}

.bulk-float-enter-active,
.bulk-float-leave-active {
  transition: opacity 0.16s ease, transform 0.18s ease;
}

.bulk-float-enter-from,
.bulk-float-leave-to {
  opacity: 0;
  transform: translate(-50%, 14px);
}

.owner-cell {
  display: inline-flex;
  min-width: 0;
  align-items: center;
  gap: 6px;
}

.owner-name {
  overflow: hidden;
  color: var(--text-soft);
  font-weight: 500;
  text-overflow: ellipsis;
}

.owner-cell .badge {
  padding: 1px 6px;
}

.user-pick {
  display: flex;
  max-height: 300px;
  flex-direction: column;
  gap: 3px;
  overflow-y: auto;
  padding: 5px;
  border: 1px solid var(--surface-border);
  border-radius: var(--radius);
  background: var(--bg-soft);
}

.user-pick-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 7px;
  background: var(--bg-elev);
  cursor: pointer;
}

.user-pick-row:hover {
  background: var(--bg-hover);
}

.user-pick-row.on {
  background: var(--accent-soft);
}

.user-pick-row .form-check-input {
  flex-shrink: 0;
  margin: 0;
}

.user-pick-avatar {
  display: grid;
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  place-items: center;
  border-radius: 7px;
  background: var(--bg-subtle);
  color: var(--text-soft);
  font-size: 11.5px;
  font-weight: 600;
}

.user-pick-avatar.admin {
  background: var(--accent);
  color: var(--on-accent);
}

.user-pick-empty {
  padding: 20px 8px;
  color: var(--text-faint);
  font-size: 12.5px;
  text-align: center;
}

.access-owner {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px;
  padding: 11px 14px;
  border: 1px solid var(--surface-border);
  border-radius: var(--radius);
  background: var(--bg-soft);
  font-size: 13px;
}

.access-label {
  color: var(--text-muted);
}

.access-owner-name {
  color: var(--text);
  font-weight: 600;
}

.access-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.access-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border: 1px solid var(--surface-border);
  border-radius: var(--radius);
  background: var(--bg-elev);
}

.access-add {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

/* ---------- 回收站 ---------- */
.trash-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.trash-table {
  overflow: hidden;
  border: 1px solid var(--surface-border);
  border-radius: var(--radius);
}
</style>
