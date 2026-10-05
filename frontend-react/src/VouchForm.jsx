import { useState } from 'react'
import { Check, Heart, Star, X } from 'lucide-react'
import { api } from './api'

export default function VouchForm({ categories, providers, vouch, initialCategory, onClose, onSave }) {
  const [category, setCategory] = useState(vouch?.category || initialCategory || categories[0]?.id || '')
  const [providerName, setProviderName] = useState(vouch?.provider_name || '')
  const [rating, setRating] = useState(vouch?.rating || 5)
  const [message, setMessage] = useState(vouch?.message || '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const providerOptions = providers.filter((provider) => provider.category === category)
  const datalistId = 'provider-options'

  async function submit(event) {
    event.preventDefault()
    if (!providerName.trim()) {
      setError('Add a provider name to continue.')
      return
    }

    setSaving(true)
    setError('')
    let createdProvider = null
    try {
      const normalizedName = providerName.trim().toLocaleLowerCase()
      let provider = providerOptions.find(
        (option) => option.name.trim().toLocaleLowerCase() === normalizedName,
      )
      if (!provider && vouch?.to_provider_id === providerName.trim()) {
        provider = { id: vouch.to_provider_id }
      }
      if (!provider) {
        provider = await api.createProvider({
          name: providerName.trim(),
          category,
          services: [],
        })
        createdProvider = provider
      }

      await onSave({
        to_provider_id: provider.id,
        category,
        rating,
        message: message.trim(),
      }, provider)
    } catch (saveError) {
      if (createdProvider?.id) {
        await api.deleteProvider(createdProvider.id).catch(() => {})
      }
      setError(saveError.message || 'Could not save this vouch.')
      setSaving(false)
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="vouch-modal" role="dialog" aria-modal="true" aria-labelledby="vouch-form-title">
        <header className="modal-heading">
          <div>
            <span className="eyebrow">A good word goes far</span>
            <h2 id="vouch-form-title">{vouch ? 'Edit your vouch' : 'Add a vouch'}</h2>
          </div>
          <button className="icon-button" type="button" aria-label="Close" onClick={onClose}><X size={18} /></button>
        </header>

        <form onSubmit={submit}>
          <label className="field-label" htmlFor="vouch-category">Service category</label>
          <select id="vouch-category" value={category} onChange={(event) => setCategory(event.target.value)} required>
            {categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>

          <label className="field-label" htmlFor="provider-name">Provider name</label>
          <input
            id="provider-name"
            list={datalistId}
            value={providerName}
            onChange={(event) => setProviderName(event.target.value)}
            placeholder="Search a name or add someone new"
            autoComplete="off"
            required
          />
          <datalist id={datalistId}>
            {providerOptions.map((provider) => <option key={provider.id} value={provider.name} />)}
          </datalist>
          <p className="field-hint">Choose an existing provider or type a new name.</p>

          <div className="rating-heading">
            <span className="field-label">Your rating</span>
            <span className="rating-number">{rating}.0 <span>/ 5</span></span>
          </div>
          <div className="rating-picker" role="radiogroup" aria-label="Rating from one to five">
            {[1, 2, 3, 4, 5].map((value) => (
              <button
                aria-label={`${value} star${value === 1 ? '' : 's'}`}
                aria-checked={rating === value}
                className={value <= rating ? 'rating-star selected' : 'rating-star'}
                key={value}
                onClick={() => setRating(value)}
                role="radio"
                type="button"
              ><Star size={22} fill={value <= rating ? 'currentColor' : 'none'} /></button>
            ))}
          </div>

          <label className="field-label" htmlFor="vouch-note">A few details <span className="optional">Optional</span></label>
          <textarea
            id="vouch-note"
            maxLength={500}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="What made them worth recommending?"
            rows={4}
            value={message}
          />
          <div className="character-count">{message.length}/500</div>

          {error && <p className="form-error" role="alert">{error}</p>}
          <footer className="modal-actions">
            <button className="button button-quiet" type="button" onClick={onClose}>Cancel</button>
            <button className="button button-primary" disabled={saving} type="submit">
              {saving ? <span className="spinner" /> : vouch ? <Check size={16} /> : <Heart size={16} fill="currentColor" />}
              {saving ? 'Saving…' : vouch ? 'Save changes' : 'Vouch for them'}
            </button>
          </footer>
        </form>
      </section>
    </div>
  )
}
