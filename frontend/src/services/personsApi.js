// Registration (INSERT) + Missing Persons list (SELECT / DELETE) on Supabase.
// No login needed: uses the public key only.
//   person = { id, name, age, gender, missingDate, missingLocation, description, photoUrl }
import { supabase, fail } from './supabaseClient';

const BUCKET = 'person-photos';
const SIGNED_URL_SECONDS = 60 * 60; // photo links valid for 1 hour

// DB row (snake_case) -> frontend object (camelCase)
const toPerson = (row, photoUrl) => ({
  id: row.id,
  name: row.name,
  age: row.age,
  gender: row.gender,
  missingDate: row.missing_date,
  missingLocation: row.missing_location,
  description: row.description || '',
  photoUrl: photoUrl || '',
  createdAt: row.created_at,
});

// REGISTER - upload photo to Storage, then insert the row
// formData fields: photo, name, age, gender, missingDate, missingLocation, description
export async function registerPerson(formData, onProgress = () => {}) {
  const file = formData.get('photo') || formData.get('photograph');
  if (!file || !file.name) throw fail(400, 'Please upload a photograph.', 'photo');
  if (!/^image\/(jpeg|png)$/.test(file.type)) throw fail(415, 'Only JPG or PNG images are allowed.', 'photo');
  if (file.size > 5 * 1024 * 1024) throw fail(413, 'Photo must be 5MB or smaller.', 'photo');

  // 1) upload photo (supabase-js has no byte-level progress, so show coarse steps)
  onProgress(10);
  const ext = file.type === 'image/png' ? 'png' : 'jpg';
  const photoPath = `registrations/${crypto.randomUUID()}.${ext}`;
  const { error: upErr } = await supabase.storage.from(BUCKET).upload(photoPath, file, {
    contentType: file.type,
    upsert: false,
  });
  if (upErr) throw fail(500, `Photo upload failed: ${upErr.message}`, 'photo');
  onProgress(70);

  // 2) insert the record
  const { data, error } = await supabase
    .from('missing_persons')
    .insert({
      name: String(formData.get('name') || '').trim(),
      age: Number(formData.get('age')),
      gender: formData.get('gender'),
      missing_date: formData.get('missingDate'),
      missing_location: String(formData.get('missingLocation') || '').trim(),
      description: String(formData.get('description') || '').trim() || null,
      photo_path: photoPath,
    })
    .select()
    .single();

  if (error) {
    // roll back the uploaded photo so no orphan files remain
    await supabase.storage.from(BUCKET).remove([photoPath]);
    if (error.code === '23505') throw fail(409, 'This person is already registered.', 'name');
    throw fail(500, error.message);
  }
  onProgress(100);
  return toPerson(data);
}

// LIST - fetch rows (+ search/filters) and attach signed photo URLs
// params: { search, gender, ageMin, ageMax, dateFrom, dateTo }
export async function getPersons(params = {}) {
  let q = supabase.from('missing_persons').select('*').order('created_at', { ascending: false });

  if (params.search) q = q.ilike('name', `%${params.search.trim()}%`);
  if (params.gender && params.gender !== 'All') q = q.eq('gender', params.gender);
  if (params.ageMin !== undefined && params.ageMin !== '') q = q.gte('age', Number(params.ageMin));
  if (params.ageMax !== undefined && params.ageMax !== '') q = q.lte('age', Number(params.ageMax));
  if (params.dateFrom) q = q.gte('missing_date', params.dateFrom);
  if (params.dateTo) q = q.lte('missing_date', params.dateTo);

  const { data: rows, error } = await q;
  if (error) throw fail(500, error.message);
  if (!rows.length) return [];

  // one batched call for all photo links
  const { data: signed } = await supabase.storage
    .from(BUCKET)
    .createSignedUrls(rows.map((r) => r.photo_path), SIGNED_URL_SECONDS);
  const urlByPath = {};
  (signed || []).forEach((s) => { if (s.signedUrl) urlByPath[s.path] = s.signedUrl; });

  return rows.map((r) => toPerson(r, urlByPath[r.photo_path]));
}

// DELETE - remove row + its photo
export async function deletePerson(id) {
  const { data: row } = await supabase.from('missing_persons').select('photo_path').eq('id', id).maybeSingle();

  const { error } = await supabase.from('missing_persons').delete().eq('id', id);
  if (error) throw fail(500, error.message);

  if (row?.photo_path) await supabase.storage.from(BUCKET).remove([row.photo_path]);
}

// COUNT - for the Dashboard "Registered Persons" card
export async function getPersonsCount() {
  const { count, error } = await supabase
    .from('missing_persons')
    .select('*', { count: 'exact', head: true });
  if (error) throw fail(500, error.message);
  return { count: count || 0 };
}
