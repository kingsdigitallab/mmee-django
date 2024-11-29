class StaticAPI {
    constructor() {
        this.response = API_PHOTOS
        // console.log(staticAPI.get_photo_urls())

        // turn url to photos relative
        this.response.data.forEach(photo => {
            photo.attributes.image = photo.attributes.image.replace('src="/media/', 'src="../media/')
            photo.attributes.url = photo.attributes.url.replace('/photos/', '')
        })
    }
    get_photo_urls() {
        return this.response.data.map(p => {
            return `<a href="${p.id}/">${p.id}</a><br>`
        }).join('\n')
    }
    filter(query) {
        // .page: 1
        // .perpage: 12
        // let ret = JSON.parse(JSON.stringify(this.response).replaceAll('height-375', 'height-700'));
        let resStr = JSON.stringify(this.response)
        if (query.imgspecs) {
            resStr = resStr.replaceAll('height-375', query.imgspecs)
        }
        let ret = JSON.parse(resStr);

        if (query.id) {
            ret.data = ret.data.filter(p => p.id == query.id)
        }

        ret.meta.query.view = query.view || 'grid';
        ret.meta.query.perpage = parseInt(query.perpage || 12);
        ret.meta.query.page = parseInt(query.page || 1);
        let start = (ret.meta.query.page - 1) * ret.meta.query.perpage
        ret.data = ret.data.slice(
            start, 
            start + ret.meta.query.perpage
        )
        ret.meta.qs = (new URLSearchParams(ret.meta.query)).toString()
        ret.meta.pagination.per_page = ret.meta.query.perpage
        ret.meta.pagination.page = ret.meta.query.page
        ret.meta.pagination.pages = Math.ceil(ret.meta.pagination.count / ret.meta.pagination.per_page)

        let q = {
            ...ret.meta.query,
            page: ret.meta.pagination.page + 1
        }
        if (q.page <= ret.meta.pagination.pages) {
            ret.links.next = '?' + (new URLSearchParams(q)).toString()
        }
        q.page = ret.meta.pagination.page - 1
        if (q.page > 0) {
            ret.links.prev = '?' + (new URLSearchParams(q)).toString()
        }
        q.page = ret.meta.pagination.pages
        ret.links.last = '?' + (new URLSearchParams(q)).toString()
        q.page = 1
        ret.links.first = '?' + (new URLSearchParams(q)).toString()

        return ret
    }
}

var staticAPI = new StaticAPI();
